import re

RANK_PATTERNS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Senior Lecturer",
    "Lecturer",
    "Research Scientist",
    "Postdoctoral",
    "Postdoctoral Fellow",
]


def extract_rank(text):
    for rank in RANK_PATTERNS:
        if re.search(rf"\b{rank}\b", text, re.IGNORECASE):
            return rank
    return None
