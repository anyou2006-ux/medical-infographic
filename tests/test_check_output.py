from __future__ import annotations

import tempfile
import unittest
import struct
from pathlib import Path

from tests._loader import load_script


check_output = load_script("check_output")


class CheckOutputTests(unittest.TestCase):
    @staticmethod
    def write_png_header(path: Path, width: int, height: int) -> None:
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height))

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

    def test_gpt_png_requires_visual_review(self):
        with tempfile.TemporaryDirectory() as temp:
            png = Path(temp) / "page-01.png"
            self.write_png_header(png, 1920, 1080)
            spec = {
                "channel": "presentation",
                "render_mode": "gpt-only",
                "sources": [{"title": "材料"}],
            }
            preview = check_output.check_outputs(spec, [png], {"status": "pass"})
            self.assertEqual(preview["status"], "warning")
            final = check_output.check_outputs(spec, [png], {"status": "pass"}, visual_reviewed=True)
            self.assertEqual(final["status"], "pass")
            self.assertEqual(final["render_mode"], "gpt-only")


if __name__ == "__main__":
    unittest.main()
