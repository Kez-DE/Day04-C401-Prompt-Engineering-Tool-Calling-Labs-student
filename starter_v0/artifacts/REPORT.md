# Day 04 Lab v2 Report — Research Agent

## Team

- Team: AI20k Day04
- Members: QuocAnh-0710
- Provider/model: openrouter / openai/gpt-4o-mini

## Final Metrics

- Final version: v3
- Final artifact_version: v3+p1fdd0591f38a+t6ae58c1c3383
- Best base run file: runs/v3_B_base_openrouter_20260602T125018727438.json
- Base case accuracy: 1.0 (20/20)
- Base tool routing accuracy: 1.0
- Base argument accuracy: 1.0
- Group eval run file: runs/v3_B_group_openrouter_20260602T125417687507.json
- Group eval accuracy: 1.0 (10/10)
- Chat transcript file: transcripts/v3_openrouter_20260602T135943183068.transcript.json

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (intentionally broken) | — | — | case=0.70, routing=0.75, args=0.70 | runs/v0_B_base_openrouter_20260602T123717244819.json |
| v1 | system_prompt.md | Prompt nói "đừng hỏi, hãy đoán" và "gửi ngay" → gây 6 lỗi. Viết lại prompt với clarify rules + scope refusal + routing rules sẽ fix tất cả. | case=0.70 | case=1.0, routing=1.0, args=1.0 | runs/v1_B_base_openrouter_20260602T124129906430.json |
| v2 | tools.yaml (policy description) | policy_area enum quá ngắn, agent không biết map câu hỏi nào vào area nào → sai policy_area trên extension eval (E01, E08). Thêm ví dụ rõ cho từng area. | extension=0.80 | extension=0.90 | runs/v2_B_extension_openrouter_20260602T124701562654.json |
| v3 | system_prompt.md + tools.yaml + hacker_news tool | E06 fail vì agent chỉ gọi 1 tool khi request ghép research+policy. Thêm rule compound-request và tool hacker_news mới. | extension=0.90 | base=1.0, extension=1.0, group=1.0 | runs/v3_B_base_openrouter_20260602T125018727438.json |

## Failure Analysis

Failures từ v0 (baseline), resolved qua v1–v3:

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix Applied |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | send(text="Nguyên hàm của x^2 là x³/3+C") | Agent dùng `send` để trả lời bài toán tích phân thay vì từ chối | v1: thêm scope refusal cho math/coding + cấm dùng send để trả lời |
| R10_missing_handle | missing_info | timeline(screenname="sama") | Không có handle → agent đoán Sam Altman | v1: thêm rule "thiếu handle → clarify, không đoán" |
| R11_missing_url | missing_info | fetch(url="https://example.com/article") | Không có URL → agent đoán URL giả | v1: thêm rule "thiếu URL → clarify" |
| R12_confirm_before_send | wrong_boundary | send(text="Bản tin này") | Agent gửi Telegram ngay không hỏi xác nhận | v1: thêm rule "trước khi send → clarify yes_no" |
| R13_parallel_web_and_tweets | wrong_tool | lookup(query="AI news", topic=None) | Bỏ `topic=news`, gộp query thành "AI news" | v1: thêm routing rule lookup cần `topic=news` cho tin tức |
| R14_out_of_scope_coding | out_of_scope | send(text="def fibonacci...") | Agent gửi code Python qua Telegram thay vì từ chối | v1: scope refusal cho coding requests |
| E01_company_source_policy | wrong_arg_value | policy(policy_area="all") | Chọn sai policy_area, không map được "tweet là fact" → source_citation | v2: mô tả chi tiết từng policy_area trong tools.yaml |
| E08_specific_url_not_arxiv | wrong_arg_value | fetch(url=...) only | Bỏ qua policy tool trong compound request | v2: fix policy_area mapping; v3: compound-request rule |
| E06_briefing_live_plus_style | wrong_tool | policy only (missing lookup) | Compound request "làm bản tin + check policy" → chỉ gọi 1 tool | v3: thêm explicit compound-request rule trong prompt |

## Team Eval Cases

10 cases trong `data/eval_group.json` — kết quả v3: 10/10 PASS:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hn_top_routing | "Hacker News" → hacker_news tool, không dùng lookup | hacker_news(feed=top) | PASS |
| G02_hn_new_feed_arg | "mới nhất" → feed=new (không dùng default top) | hacker_news(feed=new) | PASS |
| G03_hn_best_limit_arg | Trích feed=best và limit=3 từ câu hỏi | hacker_news(feed=best, limit=3) | PASS |
| G04_vague_account_clarify | Tham chiếu mơ hồ "chuyên gia AI đó" → clarify, không đoán handle | clarify(response_type=text) | PASS |
| G05_hn_and_social_parallel | Yêu cầu 2 nguồn cùng lúc → parallel call | hacker_news + social_search(query=AI) | PASS |
| G06_mt_hn_carry_limit | Multi-turn: carry limit=7 từ lượt 1, đổi feed sang new ở lượt 2 | hacker_news(feed=new, limit=7) | PASS |
| G07_mt_send_confirm_after_lookup | Sau research, user muốn gửi → hỏi xác nhận trước | clarify(response_type=yes_no) | PASS |
| G08_mt_vague_then_specify_hn | Lượt 1 mơ hồ, lượt 2 nói rõ "Hacker News" → đúng tool + args | hacker_news(feed=top, limit=5) | PASS |
| G09_mt_policy_source_citation | Multi-turn policy: lượt 2 hỏi về trích dẫn nguồn | policy(policy_area=source_citation) | PASS |
| G10_mt_hn_then_fetch | Sau HN, user cung cấp URL cụ thể → fetch đúng URL | fetch(url=https://openai.com/research/) | PASS |

## Live Chat Evidence

Transcript: `transcripts/v3_openrouter_20260602T135943183068.transcript.json`

| Turn | User Request | Tool Calls | Observed Behavior | Outcome |
|---|---|---|---|---|
| 1 | "Tin AI hom nay co gi noi bat?" | lookup(topic=news, timeframe=day) | Tìm và tóm tắt 5 tin AI hôm nay với nguồn cụ thể | ✅ Đúng tool + args |
| 2 | "Tom tat 5 tweet moi nhat giup minh" | timeline(screenname=OpenAI, limit=5) | Lấy 5 tweet từ @OpenAI | ✅ Tool đúng, limit đúng |
| 3 | "Cua Andrej Karpathy nhe" | timeline(screenname=karpathy) | Map tên "Andrej Karpathy" → handle "karpathy", carry limit=5 từ lượt trước | ✅ Multi-turn context hoạt động |
| 4 | "Dang ban tin tren len Telegram di" | clarify(response_type=yes_no) | Hỏi xác nhận trước khi gửi — KHÔNG tự gửi | ✅ Boundary đúng |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | tools/send/tool.py | Tool `send` yêu cầu `confirmed=True` — nếu agent gọi mà không có flag, tool tự động trả về `needs_confirmation`. System prompt thêm rule clarify yes_no trước khi send. | Agent hỏi xác nhận mọi lần (test tại turn 4 của transcript) |
| arXiv + company policy | tools/papers/, tools/paper_text/, tools/policy/ | 3 bonus tools hoạt động, extension eval 10/10 pass (E04–E10 cover các tool này) | policy_area mapping cần mô tả rõ trong tools.yaml |
| New tool: hacker_news | tools/hacker_news/tool.py, tools/hacker_news/TOOL.md | Dùng Hacker News public API (không cần key). Trả về top/new/best stories với score + comments. 5 group eval cases test tool này, tất cả pass. | Không có auth — rate limit của HN API có thể ảnh hưởng nếu gọi nhiều lần liên tiếp |

## Reflection

**Fixes thuộc về `system_prompt.md`:**
- Định nghĩa scope (research only, từ chối math/coding) — đây là behavioral rule, không liên quan đến một tool cụ thể.
- Clarify rules (khi nào hỏi lại, khi nào không) — logic workflow của agent.
- Compound-request rule (gọi tất cả tool khi request ghép nhiều việc) — routing strategy.
- Send boundary (luôn hỏi xác nhận trước khi dùng send tool) — safety rule.

**Fixes thuộc về `tools.yaml`:**
- Mô tả `policy_area` với ví dụ cụ thể — agent dùng description để chọn argument, không đọc system prompt khi fill args.
- Mô tả `hacker_news` với trigger keywords ("HN", "Hacker News") — giúp routing chính xác.
- Tool routing hints trong description (khi dùng `topic=news` vs `general`) — description là nơi duy nhất agent có thể biết convention này khi không có system prompt hint.

**Failure cần manual review thay vì automatic grading:**
- R10/R11 (missing handle/URL): Eval chấm "phải gọi clarify" nhưng trên thực tế có những case agent đoán đúng vẫn hữu ích cho user. Automatic grading đánh fail nhưng user experience có thể chấp nhận được.
- R13 (parallel call): Eval chấm strict về `query="AI"` vs `query="AI news"` — nhưng cả hai đều trả về kết quả tương đương. Argument matching quá strict có thể mask lỗi thật.

**What would you improve next:**
- Thêm handle lookup database trong prompt (tên → Twitter handle phổ biến) để giảm dependency vào model knowledge.
- Thêm `youtube_search` tool sử dụng Tavily với site:youtube.com để cover thêm nguồn video.
- Viết thêm multi-turn eval cases có intermediate tool results trong history (agent phải đọc kết quả từ lượt trước để quyết định lượt sau).
