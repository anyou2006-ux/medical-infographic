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


if __name__ == "__main__":
    unittest.main()

