---
name: wikipedia
track: core
kind: live_api
provider: Wikipedia REST API (public, no auth required)
requires_env: []
inputs: [query, lang, sentences]
outputs: [items]
side_effect: false
---
# wikipedia

Searches Wikipedia and returns a summary of the best matching article.

Use when the user asks about a concept, person, event, or topic and needs
background/factual information — not breaking news (use `lookup` for that)
and not academic papers (use `papers` for that).

## Parameters

- `query`: search term (e.g. "Andrej Karpathy", "Transformer neural network")
- `lang`: language code, default `"en"` (English). Use `"vi"` for Vietnamese Wikipedia.
- `sentences`: number of summary sentences to return (default 5)

## When to use

- "X là ai?" / "Who is X?" → wikipedia
- "Giải thích khái niệm Y" / "What is Y?" → wikipedia
- Breaking news / current events → use `lookup` instead
- Scientific preprints → use `papers` instead
