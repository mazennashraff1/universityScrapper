import yaml
import pandas as pd
from datetime import datetime

from crawler.university_crawler import UniversityCrawler
from scraper.fetcher import fetch
from extractor.profile_extractor import extract_profile


def main():
    # Load university list
    with open("config/universities.yaml", "r", encoding="utf-8") as f:
        universities = yaml.safe_load(f)

    # Load crawler config
    with open("config/crawler.yaml", "r", encoding="utf-8") as f:
        crawler_config = yaml.safe_load(f)

    # Load keywords for profile discovery
    with open("config/keywords.yaml", "r", encoding="utf-8") as f:
        keywords = yaml.safe_load(f)

    # Load normalization rules
    with open("config/normalization.yaml", "r", encoding="utf-8") as f:
        normalization_rules = yaml.safe_load(f)

    all_profiles = []

    for uni in universities:
        print("\n" + "=" * 70)
        print(f"University: {uni['name']} ({uni['country']})")
        print("=" * 70)

        # Initialize crawler with configs
        crawler = UniversityCrawler(
            base_url=uni["url"],
            config=crawler_config,
            keywords=keywords,
            normalization_rules=normalization_rules,
        )

        # Two-phase crawl: Find listings, then extract profiles
        candidate_urls = crawler.crawl()

        print("\n" + "-" * 70)
        print(f" Summary for {uni['name']}")
        print("-" * 70)
        print(f"Listing pages found: {len(crawler.listing_pages)}")
        print(f"Individual profiles to scrape: {len(candidate_urls)}")
        print("-" * 70)

        if not candidate_urls:
            print("  No profiles found. Check configuration or website structure.")
            continue

        # Step 2: Fetch and extract profiles
        print(f"\n Extracting data from {len(candidate_urls)} profiles...")

        for idx, url in enumerate(candidate_urls, 1):
            if idx % 10 == 0:
                print(f"  Progress: {idx}/{len(candidate_urls)} profiles processed...")

            html = fetch(url)
            if not html:
                continue

            profile = extract_profile(html, url)

            # Basic validation: must have at least name or email
            if not profile.get("name") and not profile.get("email"):
                continue

            profile["university"] = uni["name"]
            profile["country"] = uni["country"]

            all_profiles.append(profile)

            # Print extracted profile (only first 3 to avoid spam)
            if idx <= 3:
                print("\n   Profile extracted:")
                print(f"    Name: {profile.get('name', 'N/A')}")
                print(f"    Email: {profile.get('email', 'N/A')}")
                print(f"    Rank: {profile.get('rank', 'N/A')}")
                print(f"    Department: {profile.get('department', 'N/A')}")

        print(
            f"\nCompleted {uni['name']}: {len([p for p in all_profiles if p['university'] == uni['name']])} profiles extracted"
        )

    print("\n" + "=" * 70)
    print(" SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"Total profiles extracted: {len(all_profiles)}")
    print("=" * 70)

    # Export to Excel
    if all_profiles:
        export_to_excel(all_profiles)
    else:
        print("\nNo profiles found to export!")
        print("\nPossible reasons:")
        print(
            "  1. Check if 'allowed_paths' in config/crawler.yaml match your universities"
        )
        print("  2. Universities might be blocking the crawler (check robots.txt)")
        print("  3. Faculty pages might use JavaScript (not supported)")
        print("\nTry running: python test_crawler.py")
        print("to test the configuration with AUC first.")


def export_to_excel(profiles):
    """Export profiles to Excel with proper formatting"""

    # Convert interests list to string
    for profile in profiles:
        if profile.get("interests") and isinstance(profile["interests"], list):
            profile["interests"] = "; ".join(profile["interests"])
        elif not profile.get("interests"):
            profile["interests"] = ""

    # Create DataFrame with desired column order
    df = pd.DataFrame(profiles)

    # Reorder columns to match your specification
    column_order = [
        "name",
        "email",
        "rank",
        "department",
        "interests",
        "university",
        "country",
        "profile_url",
    ]

    # Ensure all columns exist
    for col in column_order:
        if col not in df.columns:
            df[col] = ""

    df = df[column_order]

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"database/academics_{timestamp}.xlsx"

    # Export to Excel with formatting
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Academics")

        # Get the worksheet
        worksheet = writer.sheets["Academics"]

        # Auto-adjust column widths
        for idx, col in enumerate(df.columns, 1):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            # Cap maximum width at 50 for readability
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length, 50)

    print(f"\nSuccessfully exported {len(profiles)} profiles to: {filename}")
    return filename


if __name__ == "__main__":
    main()
