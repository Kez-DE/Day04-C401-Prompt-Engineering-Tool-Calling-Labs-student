from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    assistant_tool_message,
    execute_tool_call,
    json_text,
    tool_results_message,
    trim_history,
)
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import load_tool_declarations, to_openai_tools


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)


st.set_page_config(page_title="Research Agent", page_icon="RA", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container { max-width: 1180px; padding-top: 1.4rem; }
    div[data-testid="stChatMessage"] { border-radius: 8px; }
    .trace-caption { color: #5f6368; font-size: 0.86rem; margin-top: -0.25rem; }
    .metric-row { border: 1px solid #e8eaed; border-radius: 8px; padding: 0.7rem 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_artifacts() -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return system_prompt, declarations, to_openai_tools(declarations)


def compact_result(value: Any, max_chars: int = 3500) -> str:
    return json_text(value, max_chars=max_chars)


def render_tool_call(call: ToolCall, event: dict[str, Any] | None = None) -> None:
    label = f"{call.name}"
    with st.expander(label, expanded=True):
        st.caption("Arguments")
        st.json(call.args)
        if event is not None:
            result = event.get("result")
            if isinstance(result, dict) and result.get("error"):
                st.error(f"{result.get('error')}: {result.get('message', '')}")
            else:
                st.caption("Result")
                st.code(compact_result(result), language="json")


def render_trace(rounds: list[dict[str, Any]] | None, tool_events: list[dict[str, Any]] | None) -> None:
    rounds = rounds or []
    tool_events = tool_events or []
    if not rounds and not tool_events:
        return

    with st.expander("Agent trace", expanded=False):
        for round_record in rounds:
            round_index = round_record.get("round", "?")
            calls = round_record.get("tool_calls", [])
            tool_results = round_record.get("tool_results", [])
            st.markdown(f"**Round {round_index}**")
            assistant_text = round_record.get("assistant_text")
            if assistant_text:
                st.caption("Model note")
                st.write(assistant_text)
            if not calls:
                st.caption("No tool call")
            for index, call_payload in enumerate(calls):
                event = tool_results[index] if index < len(tool_results) else None
                render_tool_call(ToolCall(name=call_payload["name"], args=call_payload.get("args", {})), event)

        if tool_events:
            st.divider()
            st.caption(f"Total tool events: {len(tool_events)}")


def run_model_tool_loop_live(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
) -> dict[str, Any]:
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    progress = st.status("Preparing request", expanded=True)
    trace_area = st.container()

    for round_index in range(1, max_tool_rounds + 1):
        progress.update(label=f"Round {round_index}: asking model to choose the next step", state="running")
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
            "tool_results": [],
        }

        with trace_area.container():
            st.markdown(f"#### Round {round_index}")
            if response.text:
                st.info(response.text)
            if calls:
                st.caption(f"Model selected {len(calls)} tool call(s).")
            else:
                st.success("Model answered without another tool call.")

        if not calls:
            rounds.append(round_record)
            progress.update(label="Completed", state="complete", expanded=False)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict[str, Any]] = []

        for call in calls:
            progress.update(label=f"Running tool: {call.name}", state="running")
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)

            with trace_area.container():
                render_tool_call(call, event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                rounds.append(round_record)
                progress.update(label="Waiting for user clarification", state="complete", expanded=False)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            non_clarification_events.append(event)

        rounds.append(round_record)
        working_messages.append(tool_results_message(non_clarification_events))

    progress.update(label="Stopped at max tool rounds", state="error", expanded=False)
    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds. Inspect the trace for details.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


def reset_chat() -> None:
    st.session_state.messages = []


if "messages" not in st.session_state:
    st.session_state.messages = []

system_prompt, tool_declarations, openai_tools = load_artifacts()

with st.sidebar:
    st.header("Settings")
    provider_choice = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    provider = make_provider(provider_choice)
    default_model = getattr(provider, "default_model", None) or ""
    model_choice = st.text_input("Model", value=default_model)
    history_window = st.slider("History window", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Max tool rounds", min_value=1, max_value=10, value=4)
    show_tool_catalog = st.toggle("Show tool catalog", value=True)
    st.button("Clear chat", on_click=reset_chat, use_container_width=True)

    st.divider()
    st.caption("Available tools")
    st.write(", ".join(item["name"] for item in tool_declarations))

header_left, header_right = st.columns([0.7, 0.3])
with header_left:
    st.title("Research Agent")
    st.caption("Tool-calling workspace for web, social, policy, papers, GitHub, Wikipedia, and Telegram flows.")
with header_right:
    st.metric("Tools", len(tool_declarations))
    st.metric("Messages", len(st.session_state.messages))

if show_tool_catalog:
    with st.expander("Tool catalog", expanded=False):
        cols = st.columns(3)
        for index, tool in enumerate(tool_declarations):
            with cols[index % 3]:
                st.markdown(f"**{tool['name']}**")
                st.caption(tool.get("description", "")[:180])

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"] or "")
            render_trace(msg.get("rounds"), msg.get("tool_events"))

prompt = st.chat_input("Ask for news, tweets, a URL summary, GitHub repo stats, Wikipedia background, or policy guidance")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(history, history_window),
            {"role": "user", "content": prompt},
        ]

        try:
            result = run_model_tool_loop_live(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model_choice or None,
                max_tool_rounds=max_tool_rounds,
            )

            assistant_text = result.get("assistant_text", "")
            st.divider()
            st.markdown(assistant_text or "_No text response._")

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "rounds": result.get("rounds", []),
                    "tool_events": result.get("tool_events", []),
                    "status": result.get("status"),
                }
            )
        except Exception as exc:
            error_msg = f"**Error:** {type(exc).__name__}: {str(exc)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg, "rounds": [], "tool_events": []})
