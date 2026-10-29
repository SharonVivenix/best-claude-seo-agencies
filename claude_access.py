#!/usr/bin/env python3
"""
Check what Anthropic's crawlers are allowed to fetch on a site.

    python claude_access.py example.com
    python claude_access.py example.com shop.example.com --paths / /pricing /blog/
    python claude_access.py --file domains.txt --json
    python claude_access.py example.com --strict    # exit 1 if a retrieval agent is blocked

Anthropic documents three user agents (support.claude.com, article 8896518):

    ClaudeBot         collects pages that may be used for training
    Claude-SearchBot  indexes pages to improve search results
    Claude-User       fetches a page when a Claude user asks a question

Blocking ClaudeBot is a training decision. Blocking Claude-SearchBot or
Claude-User removes the site from what Claude can look up and cite, which is
the part an agency is usually paid to improve. Older robots.txt files often
carry rules for Claude-Web or anthropic-ai instead, and those rules do not
cover the current agents. This script flags that case.

Standard library only. robots.txt is fetched once per host.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from urllib.robotparser import RobotFileParser

AGENTS = {
    "ClaudeBot": "training",
    "Claude-SearchBot": "search index",
    "Claude-User": "live fetch",
}
RETRIEVAL = ("Claude-SearchBot", "Claude-User")
LEGACY = ("Claude-Web", "anthropic-ai")
UA = "claude-access-check/1.0 (+https://github.com/SharonVivenix/best-claude-seo-agencies)"


def fetch_robots(host: str, timeout: float = 15.0) -> tuple[int, str]:
    url = f"https://{host}/robots.txt"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def named_agents(robots: str) -> set[str]:
    names = set()
    for line in robots.splitlines():
        key, _, value = line.partition(":")
        if key.strip().lower() == "user-agent":
            names.add(value.split("#")[0].strip().lower())
    return names


def audit(host: str, robots: str, status: int, paths: list[str]) -> dict:
    parser = RobotFileParser()
    if status in (401, 403):
        parser.disallow_all = True
    elif status >= 400:
        parser.allow_all = True
    else:
        parser.parse(robots.splitlines())

    named = named_agents(robots)
    result = {"host": host, "robots_status": status, "agents": {}, "warnings": []}
    for agent, role in AGENTS.items():
        blocked = [p for p in paths if not parser.can_fetch(agent, f"https://{host}{p}")]
        result["agents"][agent] = {
            "role": role,
            "named": agent.lower() in named,
            "blocked_paths": blocked,
        }

    legacy = [g for g in LEGACY if g.lower() in named]
    if legacy and not any(a.lower() in named for a in RETRIEVAL):
        result["warnings"].append(
            f"rules exist for {', '.join(legacy)} but not for Claude-SearchBot or Claude-User, "
            "so the legacy rules do not apply to current retrieval"
        )
    if status in (401, 403):
        result["warnings"].append(f"robots.txt returned {status}, crawlers treat the whole site as blocked")
    for agent in RETRIEVAL:
        if result["agents"][agent]["blocked_paths"]:
            result["warnings"].append(f"{agent} is blocked on {', '.join(result['agents'][agent]['blocked_paths'])}")
    return result


def print_report(r: dict) -> None:
    print(f"\n{r['host']}  (robots.txt HTTP {r['robots_status']})")
    print(f"  {'agent':<18}{'role':<14}{'named':<8}blocked paths")
    for agent, info in r["agents"].items():
        blocked = ", ".join(info["blocked_paths"]) or "none"
        print(f"  {agent:<18}{info['role']:<14}{'yes' if info['named'] else 'no':<8}{blocked}")
    for w in r["warnings"]:
        print(f"  ! {w}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("hosts", nargs="*")
    ap.add_argument("--file", help="one host per line")
    ap.add_argument("--paths", nargs="+", default=["/"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 when Claude-SearchBot or Claude-User is blocked")
    args = ap.parse_args()

    hosts = list(args.hosts)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            hosts += [h.strip() for h in fh if h.strip() and not h.startswith("#")]
    if not hosts:
        ap.error("give at least one host")

    reports = []
    for host in hosts:
        host = host.split("://", 1)[-1].split("/", 1)[0]
        try:
            status, robots = fetch_robots(host)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"{host}: could not fetch robots.txt ({e})", file=sys.stderr)
            continue
        reports.append(audit(host, robots, status, args.paths))

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for r in reports:
            print_report(r)

    if args.strict and any(r["agents"][a]["blocked_paths"] for r in reports for a in RETRIEVAL):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
