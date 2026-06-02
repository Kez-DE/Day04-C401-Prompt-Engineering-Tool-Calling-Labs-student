from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)


def telegram_api(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        json=payload or {},
        timeout=35,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data


def send_message(token: str, chat_id: int | str, text: str) -> None:
    chunks = split_telegram_text(text or "(empty response)")
    for chunk in chunks:
        telegram_api(
            token,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            },
        )


def split_telegram_text(text: str, limit: int = 3900) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = text
    while len(current) > limit:
        cut = current.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(current[:cut].strip())
        current = current[cut:].strip()
    if current:
        chunks.append(current)
    return chunks


def update_text(update: dict[str, Any]) -> tuple[int, str, dict[str, Any]] | None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return None
    text = message.get("text")
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None or not text:
        return None
    return int(chat_id), str(text).strip(), message


def transcript_path(transcripts_dir: Path, version: str, provider: str, chat_id: int) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version),
        safe_slug(provider),
        f"telegram_{safe_slug(str(chat_id))}",
        timestamp,
    ])
    return transcripts_dir / f"{transcript_id}.transcript.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram polling bot for the Day04 research agent.")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--transcripts-dir", type=Path, default=ROOT / "transcripts")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--poll-timeout", type=int, default=25)
    parser.add_argument("--allowed-chat-id", default=os.getenv("TELEGRAM_ALLOWED_CHAT_ID"))
    parser.add_argument("--skip-old", action="store_true", help="Advance offset past pending updates before serving.")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in starter_v0/.env")

    allowed_chat_id = str(args.allowed_chat_id).strip() if args.allowed_chat_id else ""
    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    openai_tools = to_openai_tools(load_tool_declarations(args.tools))
    provider = make_provider(args.provider)
    selected_model = args.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)

    histories: dict[int, list[dict[str, str]]] = {}
    transcript_files: dict[int, Path] = {}
    transcripts: dict[int, dict[str, Any]] = {}
    offset: int | None = None

    if args.skip_old:
        updates = telegram_api(token, "getUpdates", {"timeout": 0}).get("result", [])
        if updates:
            offset = max(int(item["update_id"]) for item in updates) + 1

    print(f"Telegram bot running. provider={args.provider} model={selected_model}")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            payload: dict[str, Any] = {"timeout": args.poll_timeout, "allowed_updates": ["message", "edited_message"]}
            if offset is not None:
                payload["offset"] = offset
            updates = telegram_api(token, "getUpdates", payload).get("result", [])

            for update in updates:
                offset = int(update["update_id"]) + 1
                parsed = update_text(update)
                if parsed is None:
                    continue
                chat_id, user_text, message = parsed

                if allowed_chat_id and str(chat_id) != allowed_chat_id:
                    send_message(token, chat_id, "Chat này chưa được cấp quyền dùng research agent.")
                    continue

                if user_text in {"/start", "/help"}:
                    send_message(
                        token,
                        chat_id,
                        "Mình là Research Agent. Gửi yêu cầu research/news/tweet/URL; mình sẽ dùng tool phù hợp và hỏi lại khi thiếu thông tin.",
                    )
                    continue
                if user_text == "/reset":
                    histories[chat_id] = []
                    send_message(token, chat_id, "Đã xoá ngữ cảnh chat cho cuộc trò chuyện này.")
                    continue

                history = histories.setdefault(chat_id, [])
                transcript_file = transcript_files.get(chat_id)
                if transcript_file is None:
                    transcript_file = transcript_path(args.transcripts_dir, args.version, args.provider, chat_id)
                    transcript_files[chat_id] = transcript_file
                    transcripts[chat_id] = {
                        "transcript_id": transcript_file.stem.removesuffix(".transcript"),
                        **artifact_version_dict(artifact_version),
                        "channel": "telegram",
                        "telegram_chat_id": chat_id,
                        "provider": args.provider,
                        "model": selected_model,
                        "system_prompt": str(args.system_prompt),
                        "tools": str(args.tools),
                        "history_window": args.history_window,
                        "max_tool_rounds": args.max_tool_rounds,
                        "created_at": now_iso(),
                        "updated_at": now_iso(),
                        "turns": [],
                    }

                turn_record: dict[str, Any] = {
                    "turn_index": len(transcripts[chat_id]["turns"]) + 1,
                    "started_at": now_iso(),
                    "telegram_message_id": message.get("message_id"),
                    "user": user_text,
                    "status": "started",
                    "assistant_text": None,
                    "rounds": [],
                    "tool_events": [],
                }

                try:
                    result = run_model_tool_loop(
                        provider=provider,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *trim_history(history, args.history_window),
                            {"role": "user", "content": user_text},
                        ],
                        tools=openai_tools,
                        model=args.model,
                        max_tool_rounds=args.max_tool_rounds,
                    )
                    turn_record.update(result)
                    assistant_text = result["assistant_text"]
                    send_message(token, chat_id, assistant_text)
                    history.append({"role": "user", "content": user_text})
                    history.append({"role": "assistant", "content": assistant_text})
                except Exception as exc:
                    turn_record.update({"status": "error", "error": f"{type(exc).__name__}: {str(exc)}"})
                    send_message(token, chat_id, f"Lỗi khi xử lý request: {type(exc).__name__}: {str(exc)}")

                turn_record["ended_at"] = now_iso()
                transcripts[chat_id]["turns"].append(turn_record)
                write_transcript(transcript_file, transcripts[chat_id])

        except KeyboardInterrupt:
            print()
            break
        except Exception as exc:
            print(f"Polling error: {type(exc).__name__}: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    main()
