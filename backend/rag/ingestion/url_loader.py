import httpx
from bs4 import BeautifulSoup
from .chunker import chunk_text

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SalesAgentBot/1.0)"
}

REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript"]


def load_url(url: str) -> list[dict]:
    """Scrape a URL and return chunk dicts."""
    try:
        response = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        raise ValueError(f"Could not fetch URL {url}: {e}")

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.body
    )

    text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    chunks = chunk_text(text)
    return [
        {
            "text": chunk,
            "metadata": {
                "source_type": "url",
                "source_name": url,
                "source_url": url,
                "chunk_index": i,
            },
        }
        for i, chunk in enumerate(chunks)
    ]
