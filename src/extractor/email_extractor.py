import re
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.edu+")


def extract_email(html):
    soup = BeautifulSoup(html, "lxml")

    # 1️⃣ mailto links
    for a in soup.select("a[href^=mailto]"):
        email = a["href"].replace("mailto:", "").strip()
        if email:
            return email

    # 2️⃣ visible text regex
    matches = EMAIL_REGEX.findall(soup.get_text(" "))
    if matches:
        return matches[0]

    return None
