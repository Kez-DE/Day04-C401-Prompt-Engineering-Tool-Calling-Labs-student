#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

".venv/bin/pip" install -r requirements.txt

SUITE="${1:-base}"
CASES="data/eval_${SUITE}.json"
if [ "$SUITE" = "group" ]; then
  CASES="data/eval_group.json"
elif [ "$SUITE" = "extension" ]; then
  CASES="data/eval_research_extension.json"
fi

exec ".venv/bin/python" run_eval.py \
  --provider openrouter \
  --model openai/gpt-oss-120b:free \
  --version v3 \
  --suite "$SUITE" \
  --eval-cases "$CASES"
