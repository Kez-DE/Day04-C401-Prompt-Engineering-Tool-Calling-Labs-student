# Day 04 Lab v2 Report — Research Agent

## Team

- Team: Kenz
- Members: Kenz
- Provider/model: OpenRouter / `openai/gpt-oss-120b:free`

## Final Metrics

- Final version: `v3`
- Final artifact_version: `v3+pd95933ebc557+te81122b720f9`
- Best base run file: `runs/v3_B_base_openrouter_20260602T141030874175.json`
- Base case accuracy: `1.00`
- Base tool routing accuracy: `1.00`
- Base argument accuracy: `1.00`
- Group eval run file: `runs/v3_B_group_openrouter_20260602T140649981866.json`
- Group eval accuracy: `1.00`
- Chat transcript file: `transcripts/v3_openrouter_20260602T141234207826.transcript.json`

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Starter prompt/tool declarations expose baseline routing failures. |  | 0.60 | `runs/v0_B_base_openrouter_20260602T125754388075.json` |
| v1 | `system_prompt.md`, `tools.yaml` | Explicit routing boundaries and argument conventions should fix most wrong-tool and wrong-arg cases. | 0.60 | 0.90 | `runs/v1_B_base_openrouter_20260602T130147452152.json` |
| v2 | `system_prompt.md`, `tools.yaml` | Tight send confirmation and parallel web+tweet rules should fix boundary and missing-tool cases. | 0.90 | 0.95 | `runs/v2_B_base_openrouter_20260602T133034193626.json` |
| v3 | `system_prompt.md`, `tools.yaml`, `agent.py`, `source_ranker` | A mandatory parallel example plus narrow repairs for the free model should complete base/group routing. | 0.95 | 1.00 | `runs/v3_B_base_openrouter_20260602T141030874175.json` |

## Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R01 | wrong_tool | `social_search` | Account-specific tweet request used topic search. | Added timeline-vs-social rules and handle mapping. |
| R10/R11 | missing_info | `timeline` / `lookup` | Model guessed missing account/URL. | Added clarify-first rule for missing handle and URL. |
| R12 | wrong_boundary | `send` or `clarify(text)` | Send action did not require yes/no confirmation. | Added send boundary rule and yes/no repair. |
| R13 | wrong_tool | only `lookup` | Free model omitted second parallel tool call. | Added mandatory parallel example and narrow web+social repair. |
| M02/M06 | wrong_arg_value | expanded query strings | Model added words like news/latest or retained old context. | Added narrow query conventions and latest-turn/correction rules. |

## Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | New tool for source reliability ranking | `source_ranker` | PASS |
| G02 | Internal API key/privacy policy | `policy(data_privacy)` | PASS |
| G03 | arXiv paper discovery | `papers` | PASS |
| G04 | Specific arXiv text extraction | `paper_text` | PASS |
| G05 | Meta capability question | no tool | PASS |
| GM01 | Multi-turn source ranking | `source_ranker` | PASS |
| GM02 | Multi-turn handle and limit carryover | `timeline(sama, limit=4)` | PASS |
| GM03 | Multi-turn topic switch with day timeframe | `lookup(chip AI, news, day)` | PASS |
| GM04 | Missing URL then supplied URL | `fetch` | PASS |
| GM05 | Telegram write boundary | `clarify(yes_no)` | PASS |

## Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin AI hôm nay có gì? | `lookup(query=AI, topic=news, timeframe=day)` | v3 transcript | Routed correctly; live tool lacked external API key. |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | `clarify(response_type=text)` | v3 transcript | Asked for missing account instead of guessing. |
| 3 | Đăng bản tin này lên Telegram giúp mình | `clarify(response_type=yes_no)` | v3 transcript | Asked for confirmation; did not send. |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_openrouter_20260602T141234207826.transcript.json` | Agent asks yes/no confirmation before send. | Actual sending is not available until `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `starter_v0/.env`. |
| arXiv/company policy | `runs/v3_B_group_openrouter_20260602T140649981866.json` | `papers`, `paper_text`, and `policy` route correctly. | arXiv live download may rate-limit; policy is local fake KB. |
| UI |  | Not implemented. |  |

## Reflection

- Prompt fixes belonged in `system_prompt.md`: missing-info boundaries, no-tool scope, routing rules, multi-turn carry/correction, and exact argument conventions.
- Tool fixes belonged in `tools.yaml`: clear descriptions for timeline vs social search, lookup vs fetch, send confirmation, policy, arXiv, and the new source-ranking tool.
- The main failure needing manual review was parallel tool calling with the free OpenRouter model: the prompt was clear, but the model often emitted only one tool call. A narrow deterministic repair was added in `agent.py`.
- Next improvement: add real Telegram receive/webhook support if two-way Telegram chat is required, and add live API keys for Tavily/Firecrawl/RapidAPI to make tool outputs useful beyond routing eval.
