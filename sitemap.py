# sitemap.py
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0; +http://example.com)"
}

async def extract_sitemap_links(site_url: str) -> set:
    parsed_links = set()
    visited = set()
    sitemap_urls = []
    parsed_url = urlparse(site_url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

    async with httpx.AsyncClient(headers=HEADERS, timeout=20) as client:
        try:
            r = await client.get(urljoin(domain, "/robots.txt"))
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        sitemap_urls.append(sitemap_url)
        except:
            pass

        if not sitemap_urls:
            sitemap_urls = [
                urljoin(domain, "/sitemap.xml"),
                urljoin(domain, "/sitemap_index.xml"),
                urljoin(domain, "/media/sitemap/sitemap.xml"),
                urljoin(domain, "/sitemaps/sitemap.xml"),
                urljoin(domain, "/sitemap/sitemap.xml")
            ]

        async def parse_sitemap(url):
            if url in visited:
                return
            visited.add(url)
            try:
                res = await client.get(url, follow_redirects=True)
                if res.status_code != 200:
                    return
                soup = BeautifulSoup(res.content, "xml")

                sitemaps = soup.find_all("sitemap")
                if sitemaps:
                    tasks = []
                    for sitemap in sitemaps:
                        loc = sitemap.find("loc")
                        if loc:
                            tasks.append(parse_sitemap(loc.text.strip()))
                    await asyncio.gather(*tasks)

                urls = soup.find_all("url")
                for url_entry in urls:
                    loc = url_entry.find("loc")
                    if loc:
                        parsed_links.add(loc.text.strip())

                for loc in soup.find_all("loc"):
                    link = loc.text.strip()
                    if link.endswith(".xml"):
                        await parse_sitemap(link)
                    else:
                        parsed_links.add(link)
            except Exception as e:
                print(f"Error parsing sitemap {url} - {e}")

        await asyncio.gather(*(parse_sitemap(s) for s in sitemap_urls))

    print(f" Total sitemap URLs collected: {len(parsed_links)}")
    return parsed_links
