import requests
from bs4 import BeautifulSoup
from ddgs import DDGS


def web_search(query: str, num_results: int = 3) -> list[str]:
    """Search DuckDuckGo and return a list of URLs."""
    urls = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=num_results)
            for r in results:
                urls.append(r["href"])
        return urls
    except Exception as e:
        return []


def read_page(url: str, **kwargs) -> str:
    """Fetch a webpage and return clean readable text."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        if len(text) < 100:
            return "Page content could not be extracted (possibly JavaScript-rendered)."

        return text[:1500]

    except Exception as e:
        return f"Could not read page: {str(e)}"