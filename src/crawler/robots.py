import urllib.robotparser as robotparser
from urllib.parse import urlparse

_parsers = {}


def is_allowed(url, user_agent):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    if base not in _parsers:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:
            return True
        _parsers[base] = rp

    return _parsers[base].can_fetch(user_agent, url)
