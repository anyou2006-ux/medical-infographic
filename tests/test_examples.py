from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._loader import ROOT, load_script


validate_content = load_script("validate_content")
render_svg = load_script("render_svg")
EXAMPLES = ROOT / "examples" / "specs"
THEMES = ROOT / "skills" / "medical-infographic" / "assets" / "themes"


class ExampleTests(unittest.TestCase):
    def test_twelve_examples_cover_all_channels_and_layouts(self):
        paths = sorted(EXAMPLES.glob("*.json"))
        self.assertEqual(len(paths), 12)
        channels = set()
        layouts = set()
        for path in paths:
            spec = json.loads(path.read_text(encoding="utf-8"))
            result = validate_content.validate_spec(spec)
            self.assertNotEqual(result["status"], "blocked", path.name)
            channels.add(spec["channel"])
            layouts.add(spec["layout"])
        self.assertEqual(channels, {"wechat-long", "xhs-cards", "presentation"})
        self.assertEqual(layouts, {"architecture", "workflow", "timeline", "matrix", "dashboard", "anatomy"})

    def test_all_examples_render_parseable_svg(self):
        for path in sorted(EXAMPLES.glob("*.json")):
            spec = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(example=path.name), tempfile.TemporaryDirectory() as temp:
                outputs = render_svg.render_infographic(spec, Path(temp), THEMES)
                expected = spec["pages"] if spec["pages"] != "auto" else (6 if spec["channel"] == "xhs-cards" else 1)
                self.assertEqual(len(outputs), expected)
                for output in outputs:
                    ET.parse(output)


if __name__ == "__main__":
    unittest.main()

