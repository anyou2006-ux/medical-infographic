from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._loader import ROOT, load_script


render_svg = load_script("render_svg")
THEMES = ROOT / "skills" / "medical-infographic" / "assets" / "themes"


def base_spec(channel: str) -> dict:
    return {
        "title": "医院数据治理架构",
        "subtitle": "从数据采集到质量管理",
        "channel": channel,
        "layout": "architecture",
        "density": "standard",
        "theme": "medical-blue",
        "evidence_mode": "balanced",
        "sections": [
            {"title": "数据源", "items": ["HIS", "EMR", "LIS"]},
            {"title": "治理平台", "items": ["主数据", "质量规则", "标准管理"]},
            {"title": "数据应用", "items": ["运营分析", "科研服务"]},
        ],
        "sources": [{"title": "示例材料", "url": "", "date": "2026-08-11"}],
    }


class RenderSvgTests(unittest.TestCase):
    def render(self, channel: str, pages="auto"):
        spec = base_spec(channel)
        spec["pages"] = pages
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return render_svg.render_infographic(spec, Path(temp.name), THEMES)

    def test_presentation_dimensions_and_xml(self):
        paths = self.render("presentation", 1)
        self.assertEqual(len(paths), 1)
        root = ET.parse(paths[0]).getroot()
        self.assertEqual(root.attrib["width"], "1920")
        self.assertEqual(root.attrib["height"], "1080")

    def test_wechat_dimensions(self):
        paths = self.render("wechat-long", 1)
        root = ET.parse(paths[0]).getroot()
        self.assertEqual(root.attrib["width"], "1080")
        self.assertEqual(root.attrib["height"], "6000")

    def test_wechat_long_uses_vertical_canvas(self):
        spec = base_spec("wechat-long")
        spec["sections"] = spec["sections"] * 2
        with tempfile.TemporaryDirectory() as temp:
            path = render_svg.render_infographic(spec, Path(temp), THEMES)[0]
            root = ET.parse(path).getroot()
            rect_y = [int(float(node.attrib["y"])) for node in root if node.tag.endswith("rect") and "y" in node.attrib]
            self.assertGreater(max(rect_y), 3500)

    def test_xhs_generates_requested_cards(self):
        paths = self.render("xhs-cards", 3)
        self.assertEqual(len(paths), 3)
        for path in paths:
            root = ET.parse(path).getroot()
            self.assertEqual(root.attrib["width"], "1080")
            self.assertEqual(root.attrib["height"], "1440")

    def test_xhs_workflow_keeps_global_sequence_numbers(self):
        spec = base_spec("xhs-cards")
        spec["layout"] = "workflow"
        spec["pages"] = 3
        with tempfile.TemporaryDirectory() as temp:
            paths = render_svg.render_infographic(spec, Path(temp), THEMES)
            second = paths[1].read_text(encoding="utf-8")
            self.assertIn("02  ", second)

    def test_escapes_xml_text(self):
        spec = base_spec("presentation")
        spec["title"] = "HIS < EMR & 数据平台"
        with tempfile.TemporaryDirectory() as temp:
            paths = render_svg.render_infographic(spec, Path(temp), THEMES)
            ET.parse(paths[0])
            raw = paths[0].read_text(encoding="utf-8")
            self.assertIn("&lt;", raw)
            self.assertIn("&amp;", raw)


if __name__ == "__main__":
    unittest.main()
