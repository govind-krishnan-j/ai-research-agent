import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


def web_search(query: str, num_results: int = 3) -> list[str]:
    """Search DuckDuckGo and return a list of URLs."""
    print(f"\n[Tool] Searching for: {query}")
    urls = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=num_results)
            for r in results:
                urls.append(r["href"])
        print(f"[Tool] Found {len(urls)} URLs")
        return urls
    except Exception as e:
        print(f"[Tool] Search error: {e}")
        return []


def read_page(url: str) -> str:
    """Fetch a webpage and return clean readable text."""
    print(f"\n[Tool] Reading: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts, styles, navbars — junk we don't need
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        # Limit to 3000 characters to avoid overloading Gemini
        return text[:3000]

    except Exception as e:
        print(f"[Tool] Read error: {e}")
        return ""