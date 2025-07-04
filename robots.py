# robots.py
import urllib.robotparser
from urllib.parse import urlparse
def is_allowed(site_url: str) -> bool:
    """Check if crawling is allowed via robots.txt"""
    parsed = urlparse(site_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = base + "/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch("*", site_url)
    except:
        return True