from __future__ import annotations

from typing import Any


HIGH_RISK_TERMS = [
    "best",
    "outperform",
    "beats",
    "all",
    "guaranteed",
    "safe",
    "legal",
    "medical",
    "financial",
    "unreleased",
    "benchmark",
]

MEDIUM_RISK_TERMS = [
    "launch",
    "release",
    "rumor",
    "viral",
    "tweet",
    "claim",
    "reported",
    "new model",
]


def check_claim(claim: str = "", context: str = "") -> dict[str, Any]:
    lowered = f"{claim} {context}".lower()
    high_hits = [term for term in HIGH_RISK_TERMS if term in lowered]
    medium_hits = [term for term in MEDIUM_RISK_TERMS if term in lowered]

    if high_hits:
        risk_level = "high"
        required_evidence = [
            "primary source or official announcement",
            "reputable independent reporting",
            "source URL attached to each factual claim",
        ]
        publish_guidance = "Do not publish as verified until tier 1/2 evidence supports the claim."
    elif medium_hits:
        risk_level = "medium"
        required_evidence = [
            "at least one reliable source",
            "clear label if the claim is early signal or unconfirmed",
        ]
        publish_guidance = "Publish only with source links and cautious wording."
    else:
        risk_level = "low"
        required_evidence = [
            "source link for factual statements",
        ]
        publish_guidance = "Low risk, but still attach sources and avoid overclaiming."

    return {
        "tool": "claim_checker",
        "claim": claim,
        "context": context,
        "risk_level": risk_level,
        "risk_signals": high_hits or medium_hits,
        "required_evidence": required_evidence,
        "publish_guidance": publish_guidance,
    }
