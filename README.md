# Best Claude SEO Agencies

<p align="center">
  <a href="https://aiclicks.io/">
    <img src="REPLACE_WITH_SCREENSHOT_URL" alt="best-claude-seo-agencies" />
  </a>
</p>

Every agency pitch for Claude work says roughly the same thing: we get you cited by Claude. Very few show a result measured on Claude alone. Of the four service agencies in this repo, none publishes a case study where the Claude number is separated from ChatGPT, Gemini or AI Overviews, and none publishes a price. So this is not a ranked list of the [best Claude SEO agencies](https://aiclicks.io/blog/best-claude-seo-agencies). It is an evidence ledger you fill with facts, a table generated from it, and two scripts that let an agency (or the client vetting one) check the parts of Claude visibility that are checkable from a terminal.

```
.
├── agencies.yaml              evidence ledger, one entry per vendor, no scores
├── render_table.py            agencies.yaml -> README table, --check, --require, --questions
├── claude_access.py           robots.txt audit for ClaudeBot, Claude-SearchBot, Claude-User
├── tracker/
│   ├── claude_rank.py         clients.yaml -> Messages API + web search -> runs.jsonl
│   ├── report.py              runs.jsonl -> mention, citation, rank, share of voice per client
│   └── clients.example.yaml   two fictional clients with prompts and competitors
├── examples/sample-runs.jsonl 84 synthetic answers for trying report.py offline
├── tests/test_offline.py      unittest, no network, no API key
└── .github/workflows/         table check, tests, link check
```

## Three paths into a Claude answer

Claude gets to your client's pages in three different ways, and Anthropic gives each one its own user agent. Per Anthropic's [crawler documentation](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler):

| User agent | What it does | What blocking it costs |
| --- | --- | --- |
| `ClaudeBot` | Collects pages that may be used for model training | Future training data. Answers from memory drift away from you over time |
| `Claude-SearchBot` | Indexes pages to improve search results | Presence in the index Claude searches when it decides to look something up |
| `Claude-User` | Fetches a page live when a user asks a question | The page itself, at the moment a buyer asks about it |

The second and third rows are the ones an agency is paid to move. The first is a policy decision the client's legal team owns.

When Claude searches during an answer, the API exposes the mechanics directly. A request with the `web_search` server tool returns `web_search_tool_result` blocks listing every URL it read, then `text` blocks whose `citations` array holds the URLs it actually credited. That split matters for reporting. A URL in the search results was read. A URL in `citations` was used. [tracker/claude_rank.py](tracker/claude_rank.py) logs both, and [tracker/report.py](tracker/report.py) only counts the second as a citation.

Two practical consequences shape the ledger below. Any vendor whose Claude page still lists `Claude-Web` is working from an older crawler list, because Anthropic now documents `Claude-SearchBot` in its place. And any case study reporting "LLM citations" or "AI visibility" as one number tells you nothing about Claude specifically, since ChatGPT volume usually dominates a blended figure.

## Evidence ledger

Generated from [agencies.yaml](agencies.yaml) by [render_table.py](render_table.py). Facts were read from each vendor's own Claude page on 29 October 2026. Vendor published scores and awards are left out on purpose. The "Open questions" column is computed from the evidence flags, never typed.

<!-- TABLE:START -->
| Vendor | Delivery | Price | Claude only proof | Crawler agents named | Open questions | Best for |
| --- | --- | --- | --- | --- | --- | --- |
| [AIclicks](https://aiclicks.io/trackers/claude-ai-tracker) | Software | $59/mo Starter, 3 day trial | Yes | None | Ask for a plan for who acts on the data | Agencies that want to run Claude tracking for many clients themselves |
| [Victorious](https://victorious.com/services/answer-engine-optimization/claude-seo/) | Agency | Not published, intake form budget brackets start at $5,000/mo | No | None | Ask for written quote, Claude only results | Enterprise brands that want named, dated case studies before signing |
| [1Digital Agency](https://www.1digitalagency.com/claude-ai-seo-services/) | Agency | Custom quote | No | `ClaudeBot`, `Claude-Web`, `Claude-User` | Ask for written quote, Claude only results, a named client, `Claude-SearchBot` rules (page lists `Claude-Web`), a shipped MCP server | Ecommerce catalogs that want crawler config and an MCP server scoped |
| [Found](https://www.found.co.uk/services/seo/ai-seo/claude-seo/) | Agency | Not published | No | None | Ask for written quote, Claude only results | UK enterprise teams adding Claude to an existing agency retainer |
| [The 66th](https://www.the66th.com/services/ai-search-optimization/claude/) | Agency | Not published, Claude work included in SEO retainers | No | None | Ask for written quote, Claude only results | Brands that refuse to pay a separate line item for Claude |
<!-- TABLE:END -->

Filter the ledger or turn it into a call checklist:

```bash
pip install pyyaml
python render_table.py --require claude_isolated price_published   # vendors that clear both bars
python render_table.py --delivery agency --questions               # one checkbox list per agency
python render_table.py --check                                     # CI: fail if README drifted from YAML
```

## Vendor notes

Four entries are Claude agencies in the service sense, meaning people do the work for you on a retainer. One is software your own team runs. They solve different problems, so decide which one you are buying before comparing prices.

**AIclicks** is software, not an agency, and it sits first because it is the only entry where the Claude number comes out separated by default. Its [Claude rank tracker](https://aiclicks.io/trackers/claude-ai-tracker) runs each tracked prompt daily, records whether the brand was mentioned or cited and which competitors and sources Claude used instead, and lets you filter all of that to Claude alone. For agencies, the useful detail is that every client gets an isolated workspace while the prompt budget is shared across them. Starter is $59/mo for 30 prompts and 3 engines, Pro is $189/mo for 150 prompts and 4 engines, Business is $499/mo for 300 prompts, 6 engines and private API access. The honest limit is the open question the table computes for it. Software shows the gap, somebody still has to write the page or earn the mention. Disclosure: AIclicks maintains the source article this repo is adapted from.

**Victorious** (founded 2013) runs Claude inside its Answer Engine Optimization practice. Its Claude page names three clients with dated numbers: Delta Electronics, Porte Brown and SimplyFun. Read the metrics before quoting them. They are conversion events, top 10 keywords, organic revenue and AI Overview citations, so they prove the agency ships SEO results, not that Claude moved. No price is published. The intake form's budget options start at $5,000 a month.

**1Digital Agency** (Philadelphia, founded 2012, ecommerce focus) has the most technical Claude page of the group. It treats each crawler as its own robots.txt task, scopes Model Context Protocol servers so Claude can query a catalog directly, and audits B2B documents for how they survive being pasted into Claude Projects. Two gaps. The page lists `Claude-Web`, which Anthropic no longer documents, and omits `Claude-SearchBot`. And no named client shows a shipped MCP server. Ask for one before paying for that line.

**Found** (London and New York, founded 2005 as Artemis Eight) bundles entity work, digital PR and LLM tracking into one Claude engagement, measured through its own Everysearch and Luminr platforms. The Mahlkönig case study reports +194% year over year blog clicks and 67% of LLM citations coming from content Found created. That second figure covers every LLM together, so ask for the Claude slice.

**The 66th** (Vancouver, boutique) does not sell Claude as a separate service at all and folds it into SEO retainers. The work it describes is concrete: rewriting ranking pages to open with a plain category statement, adding structured comparison FAQs, then building decision stage content and checking citation appearances monthly. The site discloses no founding year or team size, and both case studies on the Claude page are general SEO wins where Claude citations showed up as a side effect.

## Audit a client's Claude access before you sign

The fastest due diligence an agency can run on a new client takes one command and needs no API key:

```bash
python claude_access.py client.example --paths / /pricing /blog/ /docs/
python claude_access.py --file clients.txt --json > access.json
python claude_access.py client.example --strict    # exit 1 if Claude-SearchBot or Claude-User is blocked
```

```
www.1digitalagency.com  (robots.txt HTTP 200)
  agent             role          named   blocked paths
  ClaudeBot         training      yes     none
  Claude-SearchBot  search index  no      none
  Claude-User       live fetch    no      none
  ! rules exist for anthropic-ai but not for Claude-SearchBot or Claude-User, so the legacy rules do not apply to current retrieval
```

That is real output from 29 October 2026. Nothing is blocked there, so nothing is lost. The warning still earns its place, because the same pattern with `Disallow: /` under the legacy name is a common reason a team believes Claude is locked out (or let in) when the current agents see the opposite. The script fetches robots.txt once per host, evaluates every path against every agent with `urllib.robotparser`, and treats a 401 or 403 on robots.txt as a full block, matching how crawlers behave.

## Best Claude rank trackers for agencies

Most tools sold as the best Claude rank trackers for agencies are single brand dashboards with a workspace switcher bolted on. What an agency needs is narrower and stricter: one prompt panel per client, the same panel rerun on a schedule, results that never mix clients, and a number that is Claude only. [tracker/](tracker/) is a minimal version of that loop you own end to end.

```bash
pip install anthropic pyyaml
export ANTHROPIC_API_KEY=...
python tracker/claude_rank.py --clients tracker/clients.example.yaml --dry-run      # count calls first
python tracker/claude_rank.py --clients clients.yaml --runs 3 --out runs.jsonl
python tracker/report.py --clients clients.yaml --runs runs.jsonl
python tracker/report.py --clients clients.yaml --runs runs.jsonl --by prompt --client ledgerly
python tracker/report.py --clients clients.yaml --runs runs.jsonl --domains 10     # outreach targets
```

Each call goes to `claude-opus-5-5` through the official Anthropic SDK with the `web_search_20260209` server tool, `effort: low` to keep a daily panel cheap, server side refusal fallback switched on, and `pause_turn` handled by resending the partial turn. A client block can carry an approximate `location`, which is passed to the search tool so a Denver dental clinic is measured with Denver results.

On the bundled synthetic data, `report.py` prints:

```
| Client | Answers | Mention | Cited | Avg rank | SOV | Top rival |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ledgerly | 42 | 45% | 19% | 2.2 | 45% | Tallybook |
| northwind-dental | 42 | 60% | 31% | 1.7 | 60% | Brightsmile Clinic |
```

"Avg rank" is the position of the brand among tracked brands in order of first appearance, averaged only over answers that mention it. A rank of 1.7 with a 60% mention rate means the brand usually leads when it shows up and is missing four times in ten. Read the two numbers together.

Be clear about the limit. The API with web search is a repeatable panel, not the claude.ai app, which adds its own system prompt, memory and project files. Use the script to see trends and to sanity check a vendor's report. Once the panel grows past a few dozen prompts per client, or the client asks for ChatGPT, Gemini and Perplexity in the same report, a hosted tracker is cheaper than maintaining the plumbing.

## Questions to send before signing

```bash
python render_table.py --delivery agency --questions > questions.md
```

Beyond what the script generates, three questions separate Claude work from relabelled SEO:

1. Show me one client where you report Claude citations separately from every other engine, with dates.
2. Which user agents does your robots.txt template cover, and when did you last check it against Anthropic's list?
3. What does month three look like in numbers, and which of those numbers come from Claude alone?

## Contributing

Corrections need a URL on the vendor's own site. See [CONTRIBUTING.md](CONTRIBUTING.md). Run `python render_table.py --write` after editing [agencies.yaml](agencies.yaml) and `python -m unittest discover tests` before opening a pull request.

## Credits

Adapted from the AIclicks article on the [best Claude SEO agencies](https://aiclicks.io/blog/best-claude-seo-agencies). Vendor facts were checked on each vendor's live site on 29 October 2026 and will drift. Crawler names follow Anthropic's own documentation, which corrects the source article's use of `Claude-Web`. AIclicks is listed first and maintains the source article. Nothing here is a paid placement for the other vendors.
