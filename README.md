# **WebCrawler**

**Async Web Crawler**

This is an asynchronous web crawler built with Python. It combines sitemap parsing (via robots.txt) and fallback crawling to collect internal URLs efficiently.

## **Features**

- Automatically detects and parses `robots.txt` and sitemaps.
- Recursively follows nested sitemaps if present.
- Falls back to async crawling if sitemap is not available.
- Performs depth-limited, breadth-first crawling.
- Skips irrelevant links (e.g., images, CSS, JS, videos, fonts).
- Outputs results to `urls.json`.
- FastAPI REST API for easy integration.

## **Setup**

1. Clone this repo:

```bash
git clone https://github.com/your-username/web-crawler.git
cd web-crawler
```

2. Install dependencies:

```bash
pip install fastapi uvicorn playwright beautifulsoup4 httpx lxml
```

3. Install Playwright browser:

```bash
playwright install chromium
```

Start the server:

```bash
uvicorn main:app
```

## **Output**

Results are saved to `urls.json` containing all discovered URLs:

```json
[
  "https://example.com/",
  "https://example.com/about",
  "https://example.com/contact"
]
```
