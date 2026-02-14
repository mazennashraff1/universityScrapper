import re

DEPT_PATTERNS = [
    r"Department of ([A-Za-z &]+)",
    r"Faculty of ([A-Za-z &]+)",
    r"School of ([A-Za-z &]+)",
    r"College of ([A-Za-z &]+)",
]


def extract_department(text):
    for pattern in DEPT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
