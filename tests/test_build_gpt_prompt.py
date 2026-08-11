from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loader import load_script


build_gpt_prompt = load_script("build_gpt_prompt")


class BuildGptPromptTests(unittest.TestCase):
    def test_prompt_locks_visible_text_and_canvas(self):
        spec = {
            "title": "护理信息化架构",
            "subtitle": "业务、管理与平台",
            "channel": "presentation",
            "layout": "architecture",
            "density": "high",
            "theme": "medical-blue",
            "sections": [{"title": "移动护理", "items": ["床旁核验", "医嘱执行"]}],
            "sources": [{"title": "用户材料"}],
        }
        prompt = build_gpt_prompt.build_prompt(spec, spec["sections"], 1, 1)
        self.assertIn("1920 × 1080", prompt)
        self.assertIn('主标题："护理信息化架构"', prompt)
        self.assertIn('"床旁核验"', prompt)
        self.assertIn("逐字照抄", prompt)
        self.assertIn("不得省略文字", prompt)

    def test_writes_one_prompt_per_page(self):
        spec = {
            "title": "测试",
            "channel": "xhs-cards",
            "pages": 3,
            "sections": [
                {"title": "一", "items": ["甲"]},
                {"title": "二", "items": ["乙"]},
                {"title": "三", "items": ["丙"]},
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            paths = build_gpt_prompt.write_prompts(spec, Path(temp))
            self.assertEqual(len(paths), 3)
            self.assertTrue((Path(temp) / "gpt-prompt-manifest.json").exists())

    def test_architecture_layers_generate_grid_and_locked_labels(self):
        spec = {
            "title": "护理信息化总体架构",
            "channel": "presentation",
            "layout": "architecture",
            "density": "high",
            "sections": [
                {"layer": "临床护理应用层", "title": "护理业务", "items": ["入院评估"]},
                {"layer": "临床护理应用层", "title": "移动护理", "items": ["床旁核验"]},
                {"layer": "管理支撑层", "title": "质量安全", "items": ["规则质控"]},
                {"layer": "管理支撑层", "title": "人力排班", "items": ["能级配置"]},
            ],
        }
        prompt = build_gpt_prompt.build_prompt(spec, spec["sections"], 1, 1)
        self.assertIn('层级标签："临床护理应用层"', prompt)
        self.assertEqual(prompt.count('层级标签："临床护理应用层"'), 1)
        self.assertIn("2 行 × 2 列网格", prompt)
        self.assertIn("临床护理应用层：2 个模块", prompt)
        self.assertIn("双向细箭头", prompt)


if __name__ == "__main__":
    unittest.main()
