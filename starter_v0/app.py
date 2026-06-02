from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
)

# ── helpers ───────────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"error": "unknown_tool", "message": f"No implementation for {name}"}
    try:
        return func(**args)
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)}


def run_agent(messages: list, tools: list, provider) -> dict:
    """Single agent loop: returns {status, assistant_text, tool_events}."""
    working = list(messages)
    all_tool_events = []

    for _ in range(4):  # max 4 tool rounds
        response = provider.complete(working, tools, temperature=0.0)
        calls = response.tool_calls

        if not calls:
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "tool_events": all_tool_events,
            }

        # Build assistant message with tool call summary
        call_summary = [{"name": c.name, "args": c.args} for c in calls]
        working.append({
            "role": "assistant",
            "content": (response.text or "Calling tools…") +
                       f"\n\nTOOL_CALLS_JSON:\n{json.dumps(call_summary, ensure_ascii=False)}",
        })

        non_clarify = []
        for call in calls:
            result = execute_tool(call.name, call.args)
            event = {"tool": call.name, "args": call.args, "result": result}
            all_tool_events.append(event)

            # clarify / pause tool
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "tool_events": all_tool_events,
                }
            non_clarify.append(event)

        tool_msg = (
            "TOOL_RESULTS_JSON:\n"
            + json.dumps(non_clarify, ensure_ascii=False, indent=2)
            + "\n\nUse only these tool results. Answer the user with cited sources when available."
        )
        working.append({"role": "user", "content": tool_msg})

    return {
        "status": "max_rounds",
        "assistant_text": "Reached max tool rounds.",
        "tool_events": all_tool_events,
    }


def trim_history(history: list, window: int = 5) -> list:
    return history[-(window * 2):]


# ── session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []       # display list: {role, content, tool_events}
if "history" not in st.session_state:
    st.session_state.history = []        # LLM context history

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version_label = st.selectbox("Version", ["v3", "v2", "v1", "v0"], index=0)

    # Load artifacts
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)

    try:
        provider = make_provider(provider_name)
        artifact = build_artifact_version(version_label, system_prompt_path, tools_path)
        st.success(f"✅ {provider_name}")
        st.caption(f"`{artifact.artifact_version}`")
    except Exception as e:
        st.error(f"Provider error: {e}")
        provider = None

    st.divider()
    st.markdown("**Tools available**")
    for decl in tool_declarations:
        st.markdown(f"- `{decl['name']}`")

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

# ── main chat area ────────────────────────────────────────────────────────────
st.title("🔬 Research Agent")
st.caption("Hỏi về tin tức, tweets, arXiv papers, Wikipedia, Hacker News, và hơn thế nữa.")

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show tool calls if any
        if msg.get("tool_events"):
            for event in msg["tool_events"]:
                tool_name = event.get("tool", "?")
                args = event.get("args", {})
                result = event.get("result", {})
                items = result.get("items", [])

                with st.expander(f"🔧 `{tool_name}` — {len(items)} result(s)" if items else f"🔧 `{tool_name}`"):
                    st.json({"args": args, "result": result}, expanded=False)

# Chat input
if user_input := st.chat_input("Nhập câu hỏi của bạn…"):
    if not provider:
        st.error("Provider chưa được cấu hình. Kiểm tra API key trong .env")
        st.stop()

    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build message list for LLM
    llm_messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history),
        {"role": "user", "content": user_input},
    ]

    # Run agent with spinner
    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý…"):
            result = run_agent(llm_messages, openai_tools, provider)

        assistant_text = result["assistant_text"]
        tool_events = result["tool_events"]

        st.markdown(assistant_text)

        # Render tool calls inline
        for event in tool_events:
            tool_name = event.get("tool", "?")
            args = event.get("args", {})
            res = event.get("result", {})
            items = res.get("items", [])
            with st.expander(f"🔧 `{tool_name}` — {len(items)} result(s)" if items else f"🔧 `{tool_name}`"):
                st.json({"args": args, "result": res}, expanded=False)

    # Update state
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_text,
        "tool_events": tool_events,
    })
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": assistant_text})
