import os
import requests
from typing import Any, Dict

def run(repo_url: str) -> Dict[str, Any]:
    """
    Fetches basic information about a GitHub repository.
    """
    try:
        # Extract owner and repo from URL (e.g. https://github.com/owner/repo)
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[1].split("/")
            owner, repo = parts[0], parts[1]
        else:
            return {"error": "Invalid GitHub URL. Must contain 'github.com/'"}
            
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        headers = {}
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {
                "error": f"GitHub API error: {response.status_code}", 
                "details": response.text
            }
            
        data = response.json()
        
        return {
            "name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "url": data.get("html_url")
        }
    except Exception as e:
        return {"error": str(e)}
