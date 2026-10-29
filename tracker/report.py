#!/usr/bin/env python3
"""
Turn runs.jsonl into a per client Claude scorecard.

    python tracker/report.py --clients tracker/clients.example.yaml --runs examples/sample-runs.jsonl
    python tracker/report.py --clients clients.yaml --runs runs.jsonl --by prompt --client acme-dental
    python tracker/report.py --clients clients.yaml --runs runs.jsonl --by day
    python tracker/report.py --clients clients.yaml --runs runs.jsonl --domains 10

Metrics, all computed per answer and then averaged:

    mention   brand name or an alias appears in the answer text
    cited     a cited URL sits on one of the client's domains
    rank      position of the brand among tracked brands, ordered by first
              appearance in the text (1 = named first). Averaged only over
              answers that mention the brand, so read it next to mention rate.
    sov       answers naming the brand / answers naming any tracked brand

Standard library plus PyYAML. No network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import yaml


def pattern(names: list[str]) -> re.Pattern:
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<![\w-])(?:{alts})(?![\w-])", re.IGNORECASE)


def first_hit(rx: re.Pattern, text: str) -> int | None:
    m = rx.search(text)
    return m.start() if m else None


def host(url: str) -> str:
    h = urlparse(url).netloc.lower()
    return h[4:] if h.startswith("www.") else h


def on_domain(url: str, domains: list[str]) -> bool:
    h = host(url)
    return any(h == d or h.endswith("." + d) for d in domains)


def score(answer: dict, client: dict) -> dict:
    text = answer.get("text", "")
    brand_rx = pattern([client["brand"], *client.get("aliases", [])])
    comp_rx = {c: pattern([c]) for c in client.get("competitors", [])}

    positions = {client["brand"]: first_hit(brand_rx, text)}
    positions.update({c: first_hit(rx, text) for c, rx in comp_rx.items()})
    named = sorted((p, b) for b, p in positions.items() if p is not None)
    order = [b for _, b in named]

    domains = [d.lower().removeprefix("www.") for d in client.get("domains", [])]
    return {
        "mention": positions[client["brand"]] is not None,
        "cited": any(on_domain(u, domains) for u in answer.get("cited_urls", [])),
        "rank": order.index(client["brand"]) + 1 if client["brand"] in order else None,
        "named": order,
    }


def summarize(scored: list[dict], brand: str) -> dict:
    n = len(scored)
    ranks = [s["rank"] for s in scored if s["rank"]]
    any_brand = sum(1 for s in scored if s["named"])
    rivals = Counter(b for s in scored for b in s["named"] if b != brand)
    return {
        "answers": n,
        "mention": sum(s["mention"] for s in scored) / n if n else 0.0,
        "cited": sum(s["cited"] for s in scored) / n if n else 0.0,
        "rank": sum(ranks) / len(ranks) if ranks else None,
        "sov": sum(s["mention"] for s in scored) / any_brand if any_brand else 0.0,
        "top_rival": rivals.most_common(1)[0][0] if rivals else "",
    }


def fmt_row(key: str, m: dict) -> str:
    rank = f"{m['rank']:.1f}" if m["rank"] is not None else "n/a"
    return (f"| {key} | {m['answers']} | {m['mention']:.0%} | {m['cited']:.0%} "
            f"| {rank} | {m['sov']:.0%} | {m['top_rival'] or 'none'} |")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients", type=Path, required=True)
    ap.add_argument("--runs", type=Path, default=Path("runs.jsonl"))
    ap.add_argument("--by", choices=["client", "prompt", "day"], default="client")
    ap.add_argument("--client", help="limit to one client id")
    ap.add_argument("--domains", type=int, metavar="N", help="list the N domains Claude cites most per client")
    args = ap.parse_args()

    clients = {c["id"]: c for c in yaml.safe_load(args.clients.read_text(encoding="utf-8"))["clients"]}
    answers = [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]
    answers = [a for a in answers if a["client"] in clients and (not args.client or a["client"] == args.client)]
    if not answers:
        print("no answers matched the clients file", file=sys.stderr)
        return 1

    if args.domains:
        cites = defaultdict(Counter)
        for a in answers:
            cites[a["client"]].update(host(u) for u in a.get("cited_urls", []))
        for cid, counter in cites.items():
            print(f"\n{cid}: most cited domains")
            for dom, n in counter.most_common(args.domains):
                print(f"  {n:>4}  {dom}")
        return 0

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for a in answers:
        c = clients[a["client"]]
        key = {"client": (a["client"],), "prompt": (a["client"], a["prompt"]), "day": (a["client"], a["ts"][:10])}[args.by]
        groups[key].append(score(a, c))

    label = {"client": "Client", "prompt": "Client / prompt", "day": "Client / day"}[args.by]
    print(f"| {label} | Answers | Mention | Cited | Avg rank | SOV | Top rival |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for key in sorted(groups):
        print(fmt_row(" / ".join(key), summarize(groups[key], clients[key[0]]["brand"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
