---
name: source_ranker
track: team
kind: local_formatter
requires_env: []
inputs: [sources, purpose]
outputs: [ranked_sources, guidance]
side_effect: false
---
# source_ranker

Ranks already-known source names or URLs by evidence strength for a research
purpose. This is a local helper for source-quality planning; it does not browse
the web and does not verify facts.
