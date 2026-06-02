from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def analyze_github_repo(repo_url: str = "") -> dict[str, Any]:
    """Fetch public metadata for a GitHub repository."""
    try:
        match = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", repo_url.strip())
        if not match:
            return {"tool": "github_analyzer", "error": "Invalid GitHub URL. Must contain github.com/<owner>/<repo>."}

        owner = match.group(1)
        repo = match.group(2).removesuffix(".git")
            
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {}
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            
        response = requests.get(api_url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        return {
            "tool": "github_analyzer",
            "name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "url": data.get("html_url")
        }
    except Exception as exc:
        return err("github_analyzer", exc)
