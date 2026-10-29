#!/usr/bin/env python3
"""
Run every client's prompts through Claude with web search on, log each answer.

    pip install anthropic pyyaml
    export ANTHROPIC_API_KEY=...
    python tracker/claude_rank.py --clients tracker/clients.example.yaml --dry-run
    python tracker/claude_rank.py --clients clients.yaml --runs 3 --out runs.jsonl
    python tracker/claude_rank.py --clients clients.yaml --only acme-dental

One JSON line per answer goes to --out. tracker/report.py turns that file
into per client mention rate, citation rate, average rank and share of voice.

What this measures, honestly: the API with the web_search server tool, not
the claude.ai app. The app adds its own system prompt, memory and project
files, so its answers drift from these. Treat the numbers as a repeatable
panel you run the same way every week, not a screenshot of what one user saw.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import yaml

MODEL = "claude-opus-5-5"
SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}
MAX_CONTINUATIONS = 3  # server tool turns can stop with pause_turn


def load_clients(path: Path, only: list[str] | None) -> list[dict]:
    clients = yaml.safe_load(path.read_text(encoding="utf-8"))["clients"]
    if only:
        clients = [c for c in clients if c["id"] in only]
    for c in clients:
        for key in ("id", "brand", "prompts"):
            if key not in c:
                raise SystemExit(f"client entry is missing '{key}': {c}")
    return clients


def extract(content: list[dict]) -> dict:
    """Pull answer text, cited URLs and every searched URL out of response blocks."""
    text, cited, searched = [], [], []
    for block in content:
        kind = block.get("type")
        if kind == "text":
            text.append(block.get("text", ""))
            for c in block.get("citations") or []:
                if c.get("url") and c["url"] not in cited:
                    cited.append(c["url"])
        elif kind == "web_search_tool_result":
            results = block.get("content")
            if isinstance(results, list):  # an error result is a single object, not a list
                searched += [r["url"] for r in results if r.get("url") and r["url"] not in searched]
    return {"text": "".join(text), "cited_urls": cited, "searched_urls": searched}


def ask(client, prompt: str, location: dict | None) -> tuple[dict, dict]:
    tool = dict(SEARCH_TOOL)
    if location:
        tool["user_location"] = {"type": "approximate", **location}
    messages = [{"role": "user", "content": prompt}]
    blocks: list[dict] = []
    for _ in range(MAX_CONTINUATIONS + 1):
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            tools=[tool],
            messages=messages,
        )
        part = [b.to_dict() for b in resp.content]
        blocks += part
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": part})
    meta = {
        "stop_reason": resp.stop_reason,
        "served_by": resp.model,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return extract(blocks), meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("runs.jsonl"))
    ap.add_argument("--runs", type=int, default=1, help="repeats per prompt, 3 or more smooths out sampling noise")
    ap.add_argument("--only", nargs="+", help="client ids to run")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    clients = load_clients(args.clients, args.only)
    calls = sum(len(c["prompts"]) for c in clients) * args.runs
    print(f"{len(clients)} clients, {calls} calls to {MODEL} with web search", file=sys.stderr)
    if args.dry_run:
        for c in clients:
            print(f"  {c['id']}: {len(c['prompts'])} prompts x {args.runs} runs", file=sys.stderr)
        return 0

    import anthropic  # imported late so --dry-run and report.py work without the SDK

    api = anthropic.Anthropic()
    done = 0
    with args.out.open("a", encoding="utf-8") as fh:
        for c in clients:
            for prompt in c["prompts"]:
                for run in range(args.runs):
                    try:
                        answer, meta = ask(api, prompt, c.get("location"))
                    except anthropic.RateLimitError:
                        print("rate limited, sleeping 60s", file=sys.stderr)
                        time.sleep(60)
                        continue
                    except anthropic.APIStatusError as e:
                        print(f"{c['id']} | {prompt!r}: HTTP {e.status_code}", file=sys.stderr)
                        continue
                    row = {
                        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                        "client": c["id"],
                        "prompt": prompt,
                        "run": run,
                        "model": MODEL,
                        **meta,
                        **answer,
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    done += 1
                    if meta["stop_reason"] == "refusal":
                        print(f"{c['id']} | {prompt!r}: refused, logged with empty text", file=sys.stderr)
                    time.sleep(args.sleep)
    print(f"wrote {done} answers to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
