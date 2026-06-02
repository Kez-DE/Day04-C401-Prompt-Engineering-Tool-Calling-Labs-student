# Day 04 Lab v2 Report — Research Agent

## Team

- Team: 2 (Zone 7)
- Members:
  - Lê Quốc Anh - 2A202600824
  - Nguyễn Đức Khang - 2A202600588
  - Nguyễn Đức Mạnh - 2A202600945
- Provider/model: OpenRouter / `openai/gpt-oss-120b:free`

## Final Metrics

- Final version: `v3`
- Final artifact_version: `v3+pd988e805fa2c+ta98bf2b9cec0`
- Best base run file: `runs/v3_B_base_openrouter_20260602T155609131684.json`
- Base case accuracy: `1.00`
- Base tool routing accuracy: `1.00`
- Base argument accuracy: `1.00`
- Base multiturn accuracy: `1.00`
- Group eval run file: `runs/v3_B_group_openrouter_20260602T155304408986.json`
- Group eval accuracy: `1.00`
- Chat transcript file: `transcripts/v3_openrouter_20260602T141234207826.transcript.json`

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Starter prompt/tool declarations expose baseline routing failures. |  | 0.60 | `runs/v0_B_base_openrouter_20260602T125754388075.json` |
| v1 | `system_prompt.md`, `tools.yaml` | Explicit routing boundaries and argument conventions should fix most wrong-tool and wrong-arg cases. | 0.60 | 0.90 | `runs/v1_B_base_openrouter_20260602T130147452152.json` |
| v2 | `system_prompt.md`, `tools.yaml` | Tight send confirmation and parallel web+tweet rules should fix boundary and missing-tool cases. | 0.90 | 0.95 | `runs/v2_B_base_openrouter_20260602T133034193626.json` |
| v3 | `system_prompt.md`, `tools.yaml`, `agent.py`, `source_ranker`, `wikipedia`, `github_analyzer` | Three team tools plus narrow repairs for the free model should complete base and group routing. | 0.95 | 1.00 | `runs/v3_B_base_openrouter_20260602T155609131684.json` |

## Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R01 | wrong_tool | `social_search` | Account-specific tweet request used topic search. | Added timeline-vs-social rules and handle mapping. |
| R10/R11 | missing_info | `timeline` / `lookup` | Model guessed missing account/URL. | Added clarify-first rule for missing handle and missing URL. |
| R12 | wrong_boundary | `send` or `clarify(text)` | Send action did not require yes/no confirmation. | Added send boundary rule and yes/no repair. |
| R13 | wrong_tool | only `lookup` | Free model omitted the second parallel tool call. | Added mandatory parallel example and narrow web+social repair. |
| M02/M06 | wrong_arg_value | expanded query strings | Model added words like `news/latest` or retained old context. | Added narrow query conventions and latest-turn/correction rules. |

## Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | New tool for source reliability ranking | `source_ranker` | PASS |
| G02 | Internal API key/privacy policy | `policy(data_privacy)` | PASS |
| G03 | arXiv paper discovery | `papers` | PASS |
| G04 | Specific arXiv text extraction | `paper_text` | PASS |
| G05 | Meta capability question | no tool | PASS |
| G06 | Background encyclopedia knowledge | `wikipedia` | PASS |
| G07 | GitHub repository metadata | `github_analyzer` | PASS |
| GM01 | Multi-turn source ranking | `source_ranker` | PASS |
| GM02 | Multi-turn handle and limit carryover | `timeline(sama, limit=4)` | PASS |
| GM03 | Multi-turn topic switch with day timeframe | `lookup(chip AI, news, day)` | PASS |
| GM04 | Missing URL then supplied URL | `fetch` | PASS |
| GM05 | Telegram write boundary | `clarify(yes_no)` | PASS |

## New Tools

| Tool | Purpose | Evidence |
|---|---|---|
| `source_ranker` | Rank known sources by evidence strength for research briefs. | `G01`, `GM01` |
| `wikipedia` | Fetch encyclopedia background for concepts, people, and topics. | `G06` |
| `github_analyzer` | Fetch public metadata for GitHub repositories. | `G07` |

## Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin AI hôm nay có gì? | `lookup(query=AI, topic=news, timeframe=day)` | v3 transcript | Routed correctly; live web tool needs external API key for useful results. |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | `clarify(response_type=text)` | v3 transcript | Asked for missing account instead of guessing. |
| 3 | Đăng bản tin này lên Telegram giúp mình | `clarify(response_type=yes_no)` | v3 transcript | Asked for confirmation; did not send. |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Telegram send boundary | `transcripts/v3_openrouter_20260602T141234207826.transcript.json` | Agent asks yes/no confirmation before sending. | Actual sending requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`. |
| Telegram two-way chat runner | `telegram_bot.py` | Polls Telegram updates and replies through the research agent loop. | Should be restricted with `TELEGRAM_ALLOWED_CHAT_ID` for local testing. |
| arXiv/company policy | `runs/v3_B_group_openrouter_20260602T155304408986.json` | `papers`, `paper_text`, and `policy` route correctly. | arXiv live download may rate-limit; policy is local fake KB. |

## Reflection

- Prompt fixes belonged in `system_prompt.md`: missing-info boundaries, no-tool scope, routing rules, multi-turn carry/correction, and exact argument conventions.
- Tool fixes belonged in `tools.yaml`: timeline vs social search, lookup vs fetch, send confirmation, policy, arXiv, `source_ranker`, `wikipedia`, and `github_analyzer`.
- The main failure needing manual review was parallel tool calling with the free OpenRouter model: the prompt was clear, but the model sometimes emitted only one tool call. A narrow deterministic repair was added in `agent.py`.
- Next improvement: add production webhook deployment for Telegram and provide live API keys for Tavily, Firecrawl, and RapidAPI so final answers can use live evidence, not only routing traces.
