from __future__ import annotations

import unittest

from tests._loader import load_script


validate_content = load_script("validate_content")


class ValidateSpecTests(unittest.TestCase):
    def test_accepts_minimal_valid_spec(self):
        spec = {
            "title": "医院数据治理",
            "channel": "presentation",
            "layout": "architecture",
            "density": "standard",
            "theme": "medical-blue",
            "evidence_mode": "balanced",
            "sections": [{"title": "数据来源", "items": ["HIS", "EMR"]}],
            "sources": [{"title": "内部方案", "url": "", "date": "2026-08-11"}],
        }
        result = validate_content.validate_spec(spec)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["normalized"]["render_mode"], "gpt-only")

    def test_rejects_unknown_render_mode(self):
        result = validate_content.validate_spec(
            {"title": "测试", "channel": "presentation", "render_mode": "canvas"}
        )
        self.assertTrue(any("render_mode" in item for item in result["errors"]))

    def test_rejects_unknown_channel(self):
        result = validate_content.validate_spec({"title": "测试", "channel": "poster"})
        self.assertIn("channel", " ".join(result["errors"]))

    def test_balanced_requires_sources_for_high_risk_claims(self):
        result = validate_content.validate_content(
            "全国智慧医院 TOP 50 排名与市场份额为 35%",
            evidence_mode="balanced",
            sources=[],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("来源" in item for item in result["errors"]))

    def test_source_only_warns_instead_of_browsing(self):
        result = validate_content.validate_content(
            "某系统市场份额为 35%",
            evidence_mode="source-only",
            sources=[],
        )
        self.assertEqual(result["status"], "warning")
        self.assertTrue(result["warnings"])

    def test_blocks_common_patient_identifiers(self):
        text = "患者姓名：张三，手机号：13800138000，病历号：MR20260001"
        result = validate_content.validate_content(text, "balanced", [])
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("隐私" in item for item in result["errors"]))

    def test_allows_explicit_illustrative_data(self):
        result = validate_content.validate_content(
            "示意数据：系统覆盖率为 80%，仅用于版式演示。",
            evidence_mode="balanced",
            sources=[],
        )
        self.assertNotEqual(result["status"], "blocked")

    def test_spec_text_includes_title_subtitle_and_sections(self):
        spec = {
            "title": "护理质量驾驶舱",
            "subtitle": "示意数据，仅用于版式演示",
            "sections": [{"title": "执行质量", "items": ["医嘱执行：示意"]}],
        }
        text = validate_content.spec_text(spec)
        self.assertIn("护理质量驾驶舱", text)
        self.assertIn("示意数据", text)
        self.assertIn("医嘱执行", text)
        result = validate_content.validate_content(text, "balanced", [{"title": "虚构示例数据"}])
        self.assertEqual(result["status"], "warning")

    def test_spec_text_includes_architecture_layer(self):
        spec = {
            "title": "护理信息化架构",
            "sections": [
                {"layer": "临床护理应用层", "title": "移动护理", "items": ["床旁核验"]}
            ],
        }
        text = validate_content.spec_text(spec)
        self.assertIn("临床护理应用层", text)

    def test_rejects_non_string_layer(self):
        result = validate_content.validate_spec(
            {
                "title": "测试",
                "channel": "presentation",
                "sections": [{"layer": 1, "title": "模块", "items": []}],
            }
        )
        self.assertTrue(any("layer" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()

