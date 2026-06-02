---
name: hacker_news
track: core
kind: live_api
provider: Hacker News (public API, no auth required)
requires_env: []
inputs: [feed, limit]
outputs: [items]
side_effect: false
---
# hacker_news

Fetches top, new, or best stories from Hacker News (news.ycombinator.com).

Use when the user asks about trending tech discussions, HN posts, or Hacker News stories.
Returns a list of items with title, url, source, and a summary (score + comment count).

## Parameters

- `feed`: `top` (default) | `new` | `best`
- `limit`: number of stories to return (default 5)
