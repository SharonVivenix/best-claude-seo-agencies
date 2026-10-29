#!/usr/bin/env python3
"""
Build the evidence table in README.md from agencies.yaml.

    python render_table.py                          # print the table
    python render_table.py --write                  # rewrite the block between the markers
    python render_table.py --check                  # exit 1 if README and YAML disagree
    python render_table.py --require claude_isolated price_published
    python render_table.py --delivery agency --questions

The "Open questions" column is never typed by hand. It is derived from the
evidence flags, so it shrinks as vendors publish proof and grows when a page
names a crawler Anthropic no longer documents.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

START = "<!-- TABLE:START -->"
END = "<!-- TABLE:END -->"
HEADER = ["Vendor", "Delivery", "Price", "Claude only proof", "Crawler agents named", "Open questions", "Best for"]

# Anthropic's current crawler list. Anything else on a vendor page is legacy.
DOCUMENTED_AGENTS = {"ClaudeBot", "Claude-SearchBot", "Claude-User"}
BOOL_FIELDS = ("price_published", "claude_isolated", "mcp")


def open_questions(a: dict) -> list[str]:
    qs = []
    if a["delivery"] == "software":
        qs.append("a plan for who acts on the data")
    if not a["price_published"]:
        qs.append("written quote")
    if a["delivery"] == "agency" and not a["claude_isolated"]:
        qs.append("Claude only results")
    if not a.get("named_proof"):
        qs.append("a named client")
    legacy = [g for g in a.get("crawler_agents") or [] if g not in DOCUMENTED_AGENTS]
    if legacy:
        qs.append("`Claude-SearchBot` rules (page lists " + ", ".join(f"`{g}`" for g in legacy) + ")")
    if a.get("mcp") and not a.get("named_proof"):
        qs.append("a shipped MCP server")
    return qs


def row(a: dict) -> list[str]:
    agents = ", ".join(f"`{g}`" for g in a.get("crawler_agents") or []) or "None"
    qs = open_questions(a)
    return [
        f"[{a['name']}]({a['claude_page']})",
        a["delivery"].capitalize(),
        a["price"],
        "Yes" if a["claude_isolated"] else "No",
        agents,
        "Ask for " + ", ".join(qs) if qs else "None",
        a["best_for"],
    ]


def build_table(agencies: list[dict]) -> str:
    lines = ["| " + " | ".join(HEADER) + " |", "| " + " | ".join("---" for _ in HEADER) + " |"]
    lines += ["| " + " | ".join(row(a)) + " |" for a in agencies]
    return "\n".join(lines)


def current_block(text: str) -> str:
    if START not in text or END not in text:
        raise SystemExit("README is missing the TABLE markers.")
    return text.split(START)[1].split(END)[0].strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--questions", action="store_true", help="print the open questions per vendor as a checklist")
    ap.add_argument("--require", nargs="+", choices=BOOL_FIELDS, default=[], help="keep vendors where every flag is true")
    ap.add_argument("--delivery", choices=["software", "agency"])
    ap.add_argument("--data", type=Path, default=Path("agencies.yaml"))
    ap.add_argument("--readme", type=Path, default=Path("README.md"))
    args = ap.parse_args()

    agencies = yaml.safe_load(args.data.read_text(encoding="utf-8"))
    filtered = [
        a for a in agencies
        if all(a.get(f) for f in args.require) and (args.delivery is None or a["delivery"] == args.delivery)
    ]

    if args.questions:
        for a in filtered:
            print(f"## {a['name']}  {a['claude_page']}")
            for q in open_questions(a) or ["nothing open"]:
                print(f"- [ ] {q}")
            print()
        return 0

    table = build_table(filtered)
    if args.write or args.check:
        if args.require or args.delivery:
            raise SystemExit("--write and --check always use the full ledger, drop the filters.")
        text = args.readme.read_text(encoding="utf-8")
        if args.check:
            if current_block(text) != table:
                print("README table is stale. Run: python render_table.py --write", file=sys.stderr)
                return 1
            print("README table matches agencies.yaml")
            return 0
        head, rest = text.split(START, 1)
        tail = rest.split(END, 1)[1]
        args.readme.write_text(f"{head}{START}\n{table}\n{END}{tail}", encoding="utf-8")
        print(f"Wrote {len(filtered)} rows to {args.readme}")
        return 0

    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
