from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        response.tool_calls = repair_send_confirmation_calls(user_messages, response.tool_calls)
        response.tool_calls = repair_policy_area_calls(user_messages, response.tool_calls)
        response.tool_calls = repair_arxiv_id_calls(response.tool_calls)
        response.tool_calls = repair_parallel_web_social_calls(user_messages, response.tool_calls)
        results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})
        return AgentRun(text=response.text, tool_calls=response.tool_calls, tool_results=results)


def repair_parallel_web_social_calls(user_messages: list[dict[str, str]], calls: list[ToolCall]) -> list[ToolCall]:
    """Add an omitted complementary tool for explicit web+social requests.

    Some cheaper/free models return only the first tool call even when the request
    clearly asks for both web/news and tweets. Keep this repair narrow: it only
    triggers when the latest user-facing text contains both intents.
    """
    latest = _latest_user_text(user_messages)
    folded = _fold_text(latest)
    wants_web = "web" in folded or "news" in folded or "tin tuc" in folded or "tin ai" in folded
    wants_social = "tweet" in folded or "twitter" in folded or "social" in folded
    if not (wants_web and wants_social):
        return calls

    names = {call.name for call in calls}
    if "source_ranker" in names:
        return calls
    repaired = list(calls)
    topic = _extract_social_web_topic(latest)
    if "lookup" not in names:
        repaired.append(ToolCall(name="lookup", args={"query": topic, "topic": "news", "timeframe": "day"}))
    if "social_search" not in names:
        repaired.append(ToolCall(name="social_search", args={"query": topic}))
    return repaired


def repair_send_confirmation_calls(user_messages: list[dict[str, str]], calls: list[ToolCall]) -> list[ToolCall]:
    """Normalize send/post/publish clarification calls to yes_no confirmation."""
    latest = _latest_user_text(user_messages)
    folded = _fold_text(latest)
    wants_send = any(word in folded for word in ["send", "post", "publish", "dang", "gui", "telegram"])
    if not wants_send:
        return calls

    repaired: list[ToolCall] = []
    for call in calls:
        if call.name == "clarify" and call.args.get("response_type") != "yes_no":
            args = dict(call.args)
            args["response_type"] = "yes_no"
            repaired.append(ToolCall(name=call.name, args=args))
        else:
            repaired.append(call)
    return repaired


def repair_policy_area_calls(user_messages: list[dict[str, str]], calls: list[ToolCall]) -> list[ToolCall]:
    latest = _latest_user_text(user_messages)
    folded = _fold_text(latest)
    repaired: list[ToolCall] = []
    for call in calls:
        if call.name != "policy":
            repaired.append(call)
            continue
        args = dict(call.args)
        if any(word in folded for word in ["api key", "credential", "secret", "transcript", "privacy", "du lieu"]):
            args["policy_area"] = "data_privacy"
        elif any(word in folded for word in ["telegram", "dang", "gui", "post", "publish"]):
            args["policy_area"] = "external_publishing"
        elif any(word in folded for word in ["citation", "source", "trich dan", "nguon"]):
            args["policy_area"] = "source_citation"
        repaired.append(ToolCall(name=call.name, args=args))
    return repaired


def repair_arxiv_id_calls(calls: list[ToolCall]) -> list[ToolCall]:
    repaired: list[ToolCall] = []
    for call in calls:
        if call.name != "paper_text":
            repaired.append(call)
            continue
        args = dict(call.args)
        arxiv_url = str(args.get("arxiv_url", ""))
        match = re.search(r"(\d{4}\.\d{4,5})(?:v\d+)?", arxiv_url)
        if match:
            args["arxiv_url"] = match.group(1)
        repaired.append(ToolCall(name=call.name, args=args))
    return repaired


def _latest_user_text(user_messages: list[dict[str, str]]) -> str:
    for message in reversed(user_messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            marker = "Latest user turn to answer now:"
            if marker in content:
                return content.rsplit(marker, 1)[1].strip()
            return content
    return ""


def _extract_social_web_topic(text: str) -> str:
    folded = _fold_text(text)
    for topic in ["GPT-5", "OpenAI", "robotics", "AI"]:
        if _fold_text(topic) in folded:
            return topic
    match = re.search(r"(?:ve|about)\s+([A-Za-z0-9_.-]+)", folded)
    return match.group(1) if match else "AI"


def _fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.lower().replace("đ", "d")
