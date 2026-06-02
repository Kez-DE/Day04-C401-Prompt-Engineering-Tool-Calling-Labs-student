from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

HN_API = "https://hacker-news.firebaseio.com/v0"

FEED_MAP = {
    "top": "topstories",
    "new": "newstories",
    "best": "beststories",
}


def get_hacker_news(feed: str = "top", limit: int = 5) -> dict[str, Any]:
    try:
        feed_key = FEED_MAP.get(feed, "topstories")
        ids_resp = requests.get(f"{HN_API}/{feed_key}.json", timeout=TIMEOUT)
        ids_resp.raise_for_status()
        ids = ids_resp.json()[: int(limit or 5)]

        items = []
        for story_id in ids:
            r = requests.get(f"{HN_API}/item/{story_id}.json", timeout=TIMEOUT)
            r.raise_for_status()
            story = r.json()
            if not story or story.get("type") != "story":
                continue
            url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            items.append({
                "title": story.get("title", ""),
                "url": url,
                "source": domain(url),
                "summary": f"Score: {story.get('score', 0)} | Comments: {story.get('descendants', 0)} | By: {story.get('by', '')}",
            })

        return {"tool": "get_hacker_news", "feed": feed, "items": items}
    except Exception as exc:
        return err("get_hacker_news", exc)
