# Contributing

The ledger only holds facts a reader can verify on the vendor's own site. Corrections with a URL are the most useful contribution, because agency pages change without notice.

## Change the data, then regenerate

1. Edit [agencies.yaml](agencies.yaml). Fields: `id`, `name`, `url`, `claude_page`, `delivery`, `founded`, `price`, `price_published`, `claude_isolated`, `named_proof`, `crawler_agents`, `mcp`, `tracking`, `best_for`.
2. Do not add an open questions field. `render_table.py` derives it from the flags.
3. Run `python render_table.py --write`, then `python render_table.py --check`.
4. Open a pull request linking the vendor page that shows the change.

## Accepted

- A vendor publishing a price, or a Claude only case study. Flip the flag and link the page.
- A vendor updating its crawler list. Copy the user agents exactly as the page prints them.
- A new vendor, if it has a page dedicated to Claude work.

## Not accepted

- Ratings, scores or awards. The ledger records evidence, not opinion.
- Affiliate or tracking links.
- Results that blend Claude with other engines marked as `claude_isolated: true`.

## Code

`claude_access.py` and `tracker/report.py` stay standard library plus PyYAML and run on Python 3.9. `tracker/claude_rank.py` uses the official `anthropic` SDK. If Anthropic changes its crawler list, update `AGENTS` in `claude_access.py` from the [support article](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) and `DOCUMENTED_AGENTS` in `render_table.py` in the same commit.

```bash
pip install pyyaml
python -m unittest discover tests -v
python render_table.py --check
```
