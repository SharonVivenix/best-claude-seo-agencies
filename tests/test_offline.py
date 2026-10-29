"""Offline tests: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tracker")]

import claude_access  # noqa: E402
import claude_rank  # noqa: E402
import render_table  # noqa: E402
import report  # noqa: E402

CLIENT = {
    "id": "ledgerly",
    "brand": "Ledgerly",
    "aliases": [],
    "domains": ["ledgerly.example"],
    "competitors": ["Tallybook", "Countwise"],
}


class Report(unittest.TestCase):
    def test_rank_follows_first_appearance(self):
        s = report.score({"text": "Try Tallybook or Ledgerly. Countwise too.", "cited_urls": []}, CLIENT)
        self.assertEqual(s["named"], ["Tallybook", "Ledgerly", "Countwise"])
        self.assertEqual(s["rank"], 2)

    def test_brand_inside_a_word_is_not_a_mention(self):
        s = report.score({"text": "Ledgerlyish tools and Tallybook", "cited_urls": []}, CLIENT)
        self.assertFalse(s["mention"])
        self.assertIsNone(s["rank"])

    def test_subdomain_citation_counts(self):
        s = report.score({"text": "", "cited_urls": ["https://www.app.ledgerly.example/x"]}, CLIENT)
        self.assertTrue(s["cited"])
        s = report.score({"text": "", "cited_urls": ["https://notledgerly.example/"]}, CLIENT)
        self.assertFalse(s["cited"])


class Extract(unittest.TestCase):
    def test_citations_and_search_results(self):
        blocks = [
            {"type": "server_tool_use", "name": "web_search"},
            {"type": "web_search_tool_result", "content": [{"type": "web_search_result", "url": "https://a.example/"}]},
            {"type": "web_search_tool_result", "content": {"type": "web_search_tool_result_error", "error_code": "max_uses_exceeded"}},
            {"type": "text", "text": "Ledgerly is ", "citations": None},
            {"type": "text", "text": "popular.", "citations": [{"type": "web_search_result_location", "url": "https://a.example/"}]},
        ]
        out = claude_rank.extract(blocks)
        self.assertEqual(out["text"], "Ledgerly is popular.")
        self.assertEqual(out["cited_urls"], ["https://a.example/"])
        self.assertEqual(out["searched_urls"], ["https://a.example/"])


class Access(unittest.TestCase):
    def test_legacy_rules_do_not_cover_current_agents(self):
        robots = "User-agent: Claude-Web\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
        r = claude_access.audit("x.example", robots, 200, ["/"])
        self.assertEqual(r["agents"]["Claude-SearchBot"]["blocked_paths"], [])
        self.assertTrue(any("legacy" in w for w in r["warnings"]))

    def test_blocked_retrieval_agent_is_reported(self):
        robots = "User-agent: Claude-User\nDisallow: /pricing\n"
        r = claude_access.audit("x.example", robots, 200, ["/", "/pricing"])
        self.assertEqual(r["agents"]["Claude-User"]["blocked_paths"], ["/pricing"])
        self.assertEqual(r["agents"]["ClaudeBot"]["blocked_paths"], [])

    def test_forbidden_robots_blocks_everything(self):
        r = claude_access.audit("x.example", "", 403, ["/"])
        self.assertEqual(r["agents"]["ClaudeBot"]["blocked_paths"], ["/"])


class Ledger(unittest.TestCase):
    def test_undocumented_crawler_raises_a_question(self):
        a = {"delivery": "agency", "price_published": False, "claude_isolated": False,
             "named_proof": None, "crawler_agents": ["ClaudeBot", "Claude-Web"], "mcp": True}
        qs = render_table.open_questions(a)
        self.assertTrue(any("Claude-SearchBot" in q for q in qs))
        self.assertIn("a shipped MCP server", qs)


if __name__ == "__main__":
    unittest.main()
