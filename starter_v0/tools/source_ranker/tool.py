from __future__ import annotations

from typing import Any


SOURCE_HINTS = [
    ("official", 1),
    ("docs", 1),
    ("documentation", 1),
    ("research", 1),
    ("arxiv", 2),
    ("reuters", 2),
    ("apnews", 2),
    ("the verge", 2),
    ("tweet", 3),
    ("twitter", 3),
    ("x.com", 3),
    ("reddit", 3),
    ("forum", 3),
]


def rank_sources(sources: list[str] | None = None, purpose: str = "") -> dict[str, Any]:
    sources = sources or []
    ranked = []
    for source in sources:
        tier = 2
        lowered = source.lower()
        for hint, hinted_tier in SOURCE_HINTS:
            if hint in lowered:
                tier = hinted_tier
                break
        ranked.append(
            {
                "source": source,
                "tier": tier,
                "use": "verify factual claims" if tier <= 2 else "treat as signal only",
            }
        )

    ranked.sort(key=lambda item: (item["tier"], item["source"].lower()))
    return {
        "tool": "source_ranker",
        "purpose": purpose,
        "ranked_sources": ranked,
        "guidance": "Prefer tier 1/2 sources for factual claims; label tier 3 sources as unverified signal.",
    }
