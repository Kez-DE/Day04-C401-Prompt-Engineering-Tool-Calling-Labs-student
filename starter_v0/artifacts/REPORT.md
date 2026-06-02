# Day 04 Lab v3 Report - Research Agent

## Team

- Team: 2 (Zone 7)
- Members:
  - Lê Quốc Anh - 2A202600824
  - Nguyễn Đức Khang - 2A202600588
  - Nguyễn Đức Mạnh - 2A202600945
- Provider/model: OpenRouter / `openai/gpt-oss-120b:free`

## Completion Status

- Required lab scope: Complete.
- Bonus `send` boundary: Complete; the agent asks for explicit confirmation before Telegram/external sending.
- Bonus UI: Complete; `starter_v0/app.py` provides a Streamlit chat UI with live tool trace.
- Bonus extra tools: Complete; the project includes **4 team-added tools**, which is more than 3:
  - `source_ranker`
  - `wikipedia`
  - `github_analyzer`
  - `claim_checker`
- Telegram two-way runner: Implemented in `starter_v0/telegram_bot.py`; requires `TELEGRAM_BOT_TOKEN` and optional `TELEGRAM_ALLOWED_CHAT_ID`.

## Final Metrics

- Final version: `v3`
- Final artifact_version: `v3+pa3946a54938d+t26cb667fb1ed`
- Best base run file: `runs/v3_B_base_openrouter_20260602T171826218522.json`
- Base case accuracy: `1.00`
- Base tool routing accuracy: `1.00`
- Base argument accuracy: `1.00`
- Base multiturn accuracy: `1.00`
- Group eval run file: `runs/v3_B_group_openrouter_20260602T171438182749.json`
- Group eval accuracy: `1.00`
- Chat transcript file: `transcripts/v3_openrouter_20260602T141234207826.transcript.json`

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Starter prompt/tool declarations expose baseline routing failures. |  | 0.60 | `runs/v0_B_base_openrouter_20260602T125754388075.json` |
| v1 | `system_prompt.md`, `tools.yaml` | Explicit routing boundaries and argument conventions should fix most wrong-tool and wrong-arg cases. | 0.60 | 0.90 | `runs/v1_B_base_openrouter_20260602T130147452152.json` |
| v2 | `system_prompt.md`, `tools.yaml` | Tight send confirmation and parallel web+tweet rules should fix boundary and missing-tool cases. | 0.90 | 0.95 | `runs/v2_B_base_openrouter_20260602T133034193626.json` |
| v3 | `system_prompt.md`, `tools.yaml`, `agent.py`, team tools | Team tools plus narrow repairs for the free model should complete base and group routing. | 0.95 | 1.00 | `runs/v3_B_base_openrouter_20260602T171826218522.json` |

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
| G01 | Source reliability ranking | `source_ranker` | PASS |
| G02 | Internal API key/privacy policy | `policy(data_privacy)` | PASS |
| G03 | arXiv paper discovery | `papers` | PASS |
| G04 | Specific arXiv text extraction | `paper_text` | PASS |
| G05 | Meta capability question | no tool | PASS |
| G06 | Background encyclopedia knowledge | `wikipedia` | PASS |
| G07 | GitHub repository metadata | `github_analyzer` | PASS |
| G08 | Claim publish-readiness | `claim_checker` | PASS |
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
| `claim_checker` | Classify claim risk and required evidence before public publishing. | `G08` |

## UI And Telegram Evidence

| Feature | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Streamlit UI | `app.py` | Provides chat interface, tool catalog, live round/tool trace, tool args, and tool result panels. | Requires `streamlit` dependency and `OPENROUTER_API_KEY`. |
| Telegram send boundary | `transcripts/v3_openrouter_20260602T141234207826.transcript.json` | Agent asks yes/no confirmation before sending. | Actual sending requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`. |
| Telegram two-way chat runner | `telegram_bot.py` | Polls Telegram updates and replies through the research agent loop. | Should be restricted with `TELEGRAM_ALLOWED_CHAT_ID` for local testing. |

## Reflection

- Prompt fixes belonged in `system_prompt.md`: missing-info boundaries, no-tool scope, routing rules, multi-turn carry/correction, exact argument conventions, and publish-safety routing.
- Tool fixes belonged in `tools.yaml`: timeline vs social search, lookup vs fetch, send confirmation, policy, arXiv, `source_ranker`, `wikipedia`, `github_analyzer`, and `claim_checker`.
- The main failure needing manual review was parallel tool calling with the free OpenRouter model: the prompt was clear, but the model sometimes emitted only one tool call. A narrow deterministic repair was added in `agent.py`.
- The project now satisfies the bonus structure: UI exists and 4 new tools were added with `TOOL.md`, registry entries, and `tools.yaml` declarations.
- Next improvement: deploy Telegram via webhook and add live API keys for Tavily, Firecrawl, and RapidAPI so final answers can use live evidence, not only routing traces.
