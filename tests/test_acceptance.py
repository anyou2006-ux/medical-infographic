from __future__ import annotations

import json
import importlib.util
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tests._loader import ROOT


CASES_PATH = ROOT / "evals" / "acceptance-cases.json"


def load_acceptance_runner():
    path = ROOT / "scripts" / "run_acceptance.py"
    spec = importlib.util.spec_from_file_location("run_acceptance", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_install_verifier():
    path = ROOT / "scripts" / "verify_install.py"
    spec = importlib.util.spec_from_file_location("verify_install", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AcceptanceCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    def test_nine_cases_cover_channel_and_content_type_matrix(self):
        self.assertEqual(len(self.cases), 9)
        channels = Counter(case["expected"]["channel"] for case in self.cases)
        content_types = Counter(case["content_type"] for case in self.cases)
        self.assertEqual(channels, {"wechat-long": 3, "xhs-cards": 3, "presentation": 3})
        self.assertEqual(content_types, {"structure": 3, "process": 3, "decision": 3})
        matrix = {(case["expected"]["channel"], case["content_type"]) for case in self.cases}
        self.assertEqual(len(matrix), 9)

    def test_explicit_and_implicit_invocations_are_present(self):
        modes = {case["invocation"] for case in self.cases}
        self.assertEqual(modes, {"explicit", "implicit"})
        for case in self.cases:
            mentioned = "$medical-infographic" in case["prompt"]
            self.assertEqual(mentioned, case["invocation"] == "explicit", case["id"])

    def test_fixture_specs_match_expected_contract(self):
        for case in self.cases:
            spec_path = ROOT / case["fixture"]
            self.assertTrue(spec_path.is_file(), case["id"])
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            self.assertEqual(spec["channel"], case["expected"]["channel"], case["id"])
            self.assertEqual(spec["layout"], case["expected"]["layout"], case["id"])

    def test_runner_executes_all_nine_cases(self):
        runner = load_acceptance_runner()
        with tempfile.TemporaryDirectory() as temp:
            summary = runner.run_suite(CASES_PATH, Path(temp))
            self.assertEqual(summary["total"], 9)
            self.assertEqual(summary["passed"], 9)
            self.assertEqual(summary["failed"], 0)
            for case in self.cases:
                case_dir = Path(temp) / case["id"]
                self.assertTrue((case_dir / "content-report.json").is_file())
                self.assertTrue((case_dir / "quality-report.json").is_file())
                self.assertTrue(list(case_dir.glob("gpt-prompt-*.txt")))
                self.assertTrue(list(case_dir.glob("page-*.svg")))

    def test_install_verifier_accepts_complete_skill(self):
        verifier = load_install_verifier()
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / "medical-infographic"
            shutil.copytree(ROOT / "skills" / "medical-infographic", installed)
            source = ROOT / "skills" / "medical-infographic"
            report = verifier.verify_install(installed, source=source)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["skill_name"], "medical-infographic")
            self.assertGreaterEqual(report["files_checked"], 10)
            self.assertTrue(report["source_match"])

            skill_md = installed / "SKILL.md"
            skill_md.write_text(skill_md.read_text(encoding="utf-8").replace("\n", "\r\n"), encoding="utf-8", newline="")
            line_endings = verifier.verify_install(installed, source=source)
            self.assertEqual(line_endings["status"], "pass")
            self.assertTrue(line_endings["source_match"])

            (installed / "scripts" / "validate_content.py").write_text("changed", encoding="utf-8")
            changed = verifier.verify_install(installed, source=source)
            self.assertEqual(changed["status"], "failed")
            self.assertFalse(changed["source_match"])


if __name__ == "__main__":
    unittest.main()
