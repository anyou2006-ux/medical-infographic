from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loader import load_script


check_output = load_script("check_output")


class CheckOutputTests(unittest.TestCase):
    def test_pass_report(self):
        with tempfile.TemporaryDirectory() as temp:
            svg = Path(temp) / "page-01.svg"
            svg.write_text('<svg width="1920" height="1080"></svg>', encoding="utf-8")
            spec = {"channel": "presentation", "sources": [{"title": "材料"}]}
            report = check_output.check_outputs(spec, [svg], {"status": "pass"})
            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["layout_checked"])

    def test_missing_sources_is_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            svg = Path(temp) / "page-01.svg"
            svg.write_text('<svg width="1080" height="1440"></svg>', encoding="utf-8")
            report = check_output.check_outputs(
                {"channel": "xhs-cards", "sources": []}, [svg], {"status": "pass"}
            )
            self.assertEqual(report["status"], "warning")
            self.assertTrue(any("来源" in item for item in report["warnings"]))

    def test_privacy_block_propagates(self):
        report = check_output.check_outputs(
            {"channel": "presentation", "sources": []}, [], {"status": "blocked"}
        )
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["privacy_checked"])


if __name__ == "__main__":
    unittest.main()

