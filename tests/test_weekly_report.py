from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from weekly_report.github import TrendingParser
from weekly_report.ai import _trend_summary
from weekly_report.render import write_outputs


class TrendingParserTests(unittest.TestCase):
    def test_extracts_repository_and_weekly_stars(self):
        parser = TrendingParser()
        parser.feed('<article><h2><a href="/acme/tool"> acme / tool </a></h2><span>1,234 stars this week</span></article>')
        self.assertEqual(parser.items, [{"full_name": "acme/tool", "weekly_stars": 1234}])

    def test_ignores_sponsor_link_before_repository(self):
        parser = TrendingParser()
        parser.feed(
            '<article><a href="/sponsors/acme">Sponsor</a>'
            '<h2><a href="/acme/tool">acme/tool</a></h2>'
            '<span>99 stars this week</span></article>'
        )
        self.assertEqual(parser.items, [{"full_name": "acme/tool", "weekly_stars": 99}])


class RenderTests(unittest.TestCase):
    def test_writes_report_archive_and_snapshot(self):
        repo = {
            "rank": 1, "full_name": "acme/tool", "html_url": "https://github.com/acme/tool",
            "weekly_stars": 100, "stars": 200, "language": "Python", "license": "MIT",
            "readme": "hello",
        }
        item = {
            "full_name": "acme/tool", "tagline": "工具", "overview": "介绍", "quick_start": "运行",
            "maturity": "早期", "core_features": ["功能"], "problems": ["问题"],
            "use_cases": ["场景"], "audience": ["用户"], "differentiators": ["特点"],
            "limitations": ["限制"], "potential": ["潜力"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_outputs(root, "2026-07-18", [repo], {"trend_summary": "趋势", "top_picks": ["acme/tool"], "projects": [item]})
            self.assertTrue(path.exists())
            self.assertTrue((root / "docs" / "index.html").exists())
            self.assertTrue((root / "data" / "2026-07-18.json").exists())
            self.assertIn("acme/tool", path.read_text(encoding="utf-8"))


class AnalysisTests(unittest.TestCase):
    def test_builds_summary_from_real_metrics(self):
        repositories = [
            {"full_name": "acme/one", "weekly_stars": 120, "language": "Python"},
            {"full_name": "acme/two", "weekly_stars": 80, "language": "Rust"},
            {"full_name": "acme/three", "weekly_stars": 50, "language": "Python"},
        ]
        projects = [{"tagline": "方向一"}, {"tagline": "方向二"}, {"tagline": "方向三"}]
        summary = _trend_summary(repositories, projects)
        self.assertIn("250", summary)
        self.assertIn("acme/one", summary)
        self.assertIn("Python", summary)


if __name__ == "__main__":
    unittest.main()
