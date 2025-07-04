#crawler.py
import json
import asyncio
import sys
import time
from pathlib import Path
from bs4 import BeautifulSoup
from robots import is_allowed
from sitemap import extract_sitemap_links
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

OUTPUT_FILE = Path("urls.json")

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".js", ".css", ".ico", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".avi", ".zip", ".pdf"
)

def filter_link(href, base_url):
    if not href or href.startswith(("#", "javascript:")):
        return None
    if href.startswith("/") or not href.startswith("http"):
        href = urljoin(base_url + "/", href)
    if not href.startswith(("http://", "https://")):
        return None
    if any(href.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
        return None
    return href.strip()

def is_internal_link(link, root_domain):
    return urlparse(link).netloc == root_domain

def save_urls_to_file(urls: set):
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(urls), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to write to file: {e}")

async def scrape_links_from_page(context, url) -> set:
    links = set()
    try:
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # wait for the page to settle (JS render)
        await page.wait_for_timeout(4000)

        html = await page.content()
        await page.close()

        soup = BeautifulSoup(html, "lxml")
        base_url = url.rstrip("/")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            final_link = filter_link(href, base_url)
            if final_link:
                links.add(final_link)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return links

async def fallback_scrape(url: str) -> set:
    parsed = urlparse(url)
    root_domain = parsed.netloc
    found = set()

    if sys.platform.startswith("win"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
        )

        # Start with the main URL
        initial_links = await scrape_links_from_page(context, url)
        print(f"Found {len(initial_links)} links via initial scrape")
        found.update(initial_links)
        save_urls_to_file(found)

        visited = set([url])
        to_visit = set(link for link in initial_links if is_internal_link(link, root_domain))

        while to_visit:
            link = to_visit.pop()
            if link in visited:
                continue
            visited.add(link)
            print(f"Visiting: {link}")
            new_links = await scrape_links_from_page(context, link)
            found.update(new_links)

            # Only add internal links to be crawled further
            internal_new = set(l for l in new_links if is_internal_link(l, root_domain))
            internal_new = internal_new - visited
            to_visit.update(internal_new)

            save_urls_to_file(found)

        await browser.close()

    print(f"Recursive scraping complete. Total links: {len(found)}")
    return found

async def collect_all_links(site_url: str) -> list:
    print(f"Starting crawl for: {site_url}")
    start_time = time.time()

    if not is_allowed(site_url):
        raise Exception("Crawling disallowed by robots.txt")

    all_links = set()

    try:
        sitemap_links = await extract_sitemap_links(site_url)
        if sitemap_links:
            all_links.update(sitemap_links)
            print(f"Found {len(sitemap_links)} links from sitemap")
        else:
            print("No links found in sitemap")
    except Exception as e:
        print(f"Sitemap extraction failed: {e}")

    if not all_links:
        print("Sitemap not found or empty, falling back to scraping page...")
        try:
            scraped_links = await fallback_scrape(site_url)
            all_links.update(scraped_links)
            print(f"Found {len(scraped_links)} links from recursive scraping")
        except Exception as e:
            print(f"Scraping failed: {e}")
            raise Exception(f"Both sitemap and scraping failed: {e}")

    save_urls_to_file(all_links)
    elapsed = time.time() - start_time
    print(f"Saved {len(all_links)} links to {OUTPUT_FILE}")
    print(f"Total crawl time: {elapsed:.2f} seconds")
    return list(all_links)
