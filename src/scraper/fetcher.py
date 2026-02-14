import requests
from utils.logger import get_logger

logger = get_logger("Fetcher")

HEADERS = {"User-Agent": "AcademicCrawler/1.0 (Academic Collaboration; non-commercial)"}


def fetch(url, timeout=15):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
    return None
