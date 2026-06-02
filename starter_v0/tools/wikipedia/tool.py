from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

WIKI_API = "https://en.wikipedia.org/api/rest_v1"
WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "AI20k-Research-Agent/1.0 (educational lab)"}


def wikipedia_search(query: str = "", lang: str = "en", sentences: int = 5) -> dict[str, Any]:
    try:
        # Step 1: search for the best matching article title
        search_resp = requests.get(
            WIKI_SEARCH,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
                "utf8": 1,
            },
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        search_resp.raise_for_status()
        results = search_resp.json().get("query", {}).get("search", [])
        if not results:
            return {"tool": "wikipedia_search", "query": query, "items": []}

        title = results[0]["title"]

        # Step 2: fetch the article summary
        base = f"https://{lang}.wikipedia.org/api/rest_v1"
        summary_resp = requests.get(
            f"{base}/page/summary/{requests.utils.quote(title)}",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        summary_resp.raise_for_status()
        data = summary_resp.json()

        # Trim to requested number of sentences
        extract = data.get("extract", "")
        if sentences and sentences > 0:
            parts = extract.split(". ")
            extract = ". ".join(parts[:sentences]).strip()
            if extract and not extract.endswith("."):
                extract += "."

        item = {
            "title": data.get("title", title),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", f"https://{lang}.wikipedia.org/wiki/{title}"),
            "source": f"{lang}.wikipedia.org",
            "summary": extract,
            "description": data.get("description", ""),
        }
        return {"tool": "wikipedia_search", "query": query, "items": [item]}
    except Exception as exc:
        return err("wikipedia_search", exc)
