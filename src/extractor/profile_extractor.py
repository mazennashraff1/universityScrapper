from bs4 import BeautifulSoup

from extractor.email_extractor import extract_email
from extractor.rank_extractor import extract_rank
from extractor.department_extractor import extract_department
from extractor.interest_extractor import extract_interests


def extract_profile(html, url):
    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text(" ", strip=True)

    profile = {
        "name": extract_name(soup),
        "email": extract_email(html),
        "rank": extract_rank(full_text),
        "department": extract_department(full_text),
        "interests": extract_interests(html),
        "profile_url": url,
    }

    return profile


def extract_name(soup):
    if soup.h1:
        return soup.h1.get_text(strip=True)

    if soup.h2:
        return soup.h2.get_text(strip=True)

    if soup.title:
        return soup.title.get_text(strip=True).split("|")[0]

    return None
