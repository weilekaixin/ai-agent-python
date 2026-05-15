import re
import urllib.parse
from html import unescape

import httpx
from bs4 import BeautifulSoup


def scrape_search(url_template: str, query: str) -> str:
    """通用搜索引擎爬虫"""
    url = url_template.replace("{query}", urllib.parse.quote(query))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
    resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li.b_algo")

    results = []
    for i, li in enumerate(items):
        title_el = li.select_one("h2 a")
        snippet_el = li.select_one(".b_caption p")

        if title_el:
            title = unescape(title_el.get_text(strip=True))
            link = title_el.get("href", "")
            snippet = unescape(snippet_el.get_text(strip=True)) if snippet_el else ""
            snippet = re.sub(r"\s+", " ", snippet)
            results.append(f"{title}\n{snippet}\n{link}")

    return "\n---\n".join(results) if results else "未找到相关结果"
