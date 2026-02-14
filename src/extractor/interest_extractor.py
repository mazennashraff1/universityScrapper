from bs4 import BeautifulSoup

INTEREST_KEYWORDS = [
    "research interests",
    "areas of interest",
    "research focus",
    "research areas",
]


def extract_interests(html):
    soup = BeautifulSoup(html, "lxml")
    interests = []

    for header in soup.find_all(["h2", "h3", "strong"]):
        header_text = header.get_text(strip=True).lower()

        if any(key in header_text for key in INTEREST_KEYWORDS):
            section = header.find_next_sibling()
            if section:
                text = section.get_text(" ", strip=True)
                interests.extend(split_interests(text))

    return list(set(interests)) if interests else None


def split_interests(text):
    separators = [",", ";", "•", "|"]
    for sep in separators:
        if sep in text:
            return [t.strip() for t in text.split(sep) if len(t.strip()) > 3]

    return [text] if len(text) > 5 else []
