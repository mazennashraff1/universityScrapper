from urllib.parse import urljoin, urlparse
from collections import deque
from bs4 import BeautifulSoup

from crawler.robots import is_allowed
from utils.rate_limiter import RateLimiter
from utils.logger import get_logger
from scraper.fetcher import fetch


class UniversityCrawler:
    def __init__(self, base_url, config, keywords, normalization_rules):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(self.base_url).netloc

        self.max_depth = config.get("max_depth", 2)
        self.allowed_paths = config.get("allowed_paths", [])
        self.delay = config.get("delay_seconds", 3)

        self.keywords = keywords
        self.normalization_rules = normalization_rules

        self.visited = set()
        self.listing_pages = set()  # Pages that contain faculty listings
        self.profile_urls = set()  # Individual profile pages

        self.rate_limiter = RateLimiter(self.delay)
        self.logger = get_logger("UniversityCrawler")

    def crawl(self):
        """
        Two-phase crawl:
        Phase 1: Find listing pages (pages with keywords like 'faculty-profiles', 'people', etc.)
        Phase 2: Extract all profile links from listing pages
        """

        print("\n" + "=" * 70)
        print("PHASE 1: Finding Faculty Listing Pages")
        print("=" * 70)

        # Phase 1: Find listing pages
        self._find_listing_pages()

        print("\n" + "=" * 70)
        print(
            f"PHASE 2: Extracting Individual Profiles from {len(self.listing_pages)} Listing Pages"
        )
        print("=" * 70)

        # Phase 2: Extract profiles from listing pages
        self._extract_profiles_from_listings()

        print("\n" + "=" * 70)
        print(f"COMPLETE: Found {len(self.profile_urls)} individual profiles")
        print("=" * 70)

        self.logger.info(
            f"Finished {self.base_url} | "
            f"listing_pages={len(self.listing_pages)} | "
            f"profiles={len(self.profile_urls)}"
        )

        return list(self.profile_urls)

    def _find_listing_pages(self):
        """Phase 1: Find pages that contain faculty listings"""
        queue = deque([(self.base_url, 0)])
        self.logger.info(
            f"Phase 1: Starting listing page discovery from {self.base_url}"
        )

        while queue:
            url, depth = queue.popleft()

            if depth > self.max_depth or url in self.visited:
                continue

            if not is_allowed(url, "AcademicCrawler"):
                print(f"  [SKIP] Blocked by robots.txt: {url}")
                continue

            self.visited.add(url)
            print(f"\n  [PHASE 1 - DEPTH {depth}] Checking: {url}")
            self.rate_limiter.wait()

            html = fetch(url)
            if not html:
                print(f"  [FAIL] Could not fetch: {url}")
                continue

            soup = BeautifulSoup(html, "lxml")

            # Check if this is a listing page
            if self._is_listing_page(url):
                self.listing_pages.add(url)
                print(f"  [LISTING PAGE FOUND] {url}")
                self.logger.info(f"Found listing page: {url}")

            # Continue searching for more listing pages
            links = soup.find_all("a", href=True)

            for a in links:
                href = a["href"]
                absolute = urljoin(url, href)
                normalized = self._normalize(absolute)

                if not normalized or normalized in self.visited:
                    continue

                # Only follow links that might lead to listing pages
                if self._might_lead_to_listing(normalized):
                    queue.append((normalized, depth + 1))

    def _extract_profiles_from_listings(self):
        """Phase 2: Extract all individual profile links from listing pages safely with pagination"""

        queue = deque(self.listing_pages)  # start with all known listing pages
        visited = set()  # keep track of processed pages

        while queue:
            listing_url = queue.popleft()
            if listing_url in visited:
                continue
            visited.add(listing_url)

            print(f"\n[PROCESSING] {listing_url}")

            # Rate limiting
            self.rate_limiter.wait()

            # Fetch HTML
            html = fetch(listing_url)
            if not html:
                print(f"  [FAIL] Could not fetch listing page: {listing_url}")
                continue

            soup = BeautifulSoup(html, "lxml")
            links = soup.find_all("a", href=True)

            profiles_found = 0

            # Extract individual profile links
            for a in links:
                href = a["href"]
                absolute = urljoin(listing_url, href)
                normalized = self._normalize(absolute)

                if not normalized:
                    continue

                if self._is_profile_link(normalized, a.text):
                    if normalized not in self.profile_urls:
                        self.profile_urls.add(normalized)
                        profiles_found += 1
                        print(f"    Profile: {normalized}")

            print(f"  [TOTAL FROM THIS PAGE] {profiles_found} profiles")

            # Handle pagination links safely
            pagination_links = self._find_pagination_links(soup, listing_url)
            for page_url in pagination_links:
                if page_url not in visited and page_url not in queue:
                    queue.append(page_url)
                    self.listing_pages.add(page_url)  # keep the master set
                    print(f"  [PAGINATION] Found next page: {page_url}")

    def _is_listing_page(self, url):
        """Check if URL is a faculty listing page based on keywords"""
        path = urlparse(url).path.lower()

        # Check if URL contains any of the allowed paths/keywords
        for keyword in self.allowed_paths:
            if keyword.lower() in path:
                return True

        return False

    def _might_lead_to_listing(self, url):
        """Check if URL might lead to a listing page"""
        path = urlparse(url).path.lower()

        # Allow navigation through directories that might contain listings
        for keyword in self.allowed_paths:
            if keyword.lower() in path:
                return True

        # Also check for common navigation keywords
        nav_keywords = [
            "about",
            "academics",
            "research",
            "school",
            "department",
            "college",
        ]
        for keyword in nav_keywords:
            if keyword in path:
                return True

        return False

    def _is_profile_link(self, url, link_text=""):
        """
        Check if a link is an individual profile page.
        Profile links are typically:
        - Under the same domain as listing page
        - Not the listing page itself
        - Not navigation/utility links
        """
        path = urlparse(url).path.lower()

        # Skip if it's the listing page itself
        if url in self.listing_pages:
            return False

        # Skip common non-profile paths
        skip_patterns = [
            "login",
            "search",
            "contact",
            "about",
            "news",
            "events",
            "calendar",
            "resources",
            "apply",
            "admissions",
            "donate",
            ".pdf",
            ".doc",
            ".jpg",
            ".png",
            "mailto:",
            "tel:",
            "twitter",
            "facebook",
            "linkedin",
            "instagram",
        ]

        for pattern in skip_patterns:
            if pattern in path or pattern in url.lower():
                return False

        # If the link is from a listing page and has a path structure, it's likely a profile
        # Example: /fac/john-doe or /faculty/jane-smith or /people/dr-ahmed
        if "/" in path and len(path.strip("/")) > 0:
            # Check if it's a reasonable length for a profile URL
            path_parts = [p for p in path.split("/") if p]
            if len(path_parts) >= 1 and len(path_parts) <= 5:
                return True

        return False

    def _find_pagination_links(self, soup, current_url):
        """Find pagination links (next page, page 2, etc.)"""
        pagination_urls = []

        # Look for common pagination patterns
        pagination_indicators = ["next", "page", "›", "»", ">"]

        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True).lower()
            href = a["href"]

            # Check if it's a pagination link
            is_pagination = False
            for indicator in pagination_indicators:
                if indicator in link_text or indicator in href.lower():
                    is_pagination = True
                    break

            # Also check for numbered pages
            if link_text.isdigit():
                is_pagination = True

            if is_pagination:
                absolute = urljoin(current_url, href)
                normalized = self._normalize(absolute)

                if normalized and self._is_listing_page(normalized):
                    pagination_urls.append(normalized)

        return pagination_urls

    def _normalize(self, url):
        """Normalize URLs according to rules"""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        if parsed.netloc != self.domain:
            return None

        path = parsed.path.rstrip("/")

        # Apply optional normalization rules
        for rule in self.normalization_rules.get("replace", []):
            path = path.replace(rule.get("from", ""), rule.get("to", ""))

        return f"{parsed.scheme}://{parsed.netloc}{path}"
