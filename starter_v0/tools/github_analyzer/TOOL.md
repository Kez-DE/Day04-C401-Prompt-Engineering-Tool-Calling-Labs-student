---
name: github_analyzer
track: team
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [repo_url]
outputs: [name, description, stars, forks, open_issues, language, url]
side_effect: false
---

# github_analyzer

Fetches public metadata for a GitHub repository: stars, forks, issues, main
language, description, and URL. It can use `GITHUB_TOKEN` for higher rate limits
but does not require one for light classroom use.
