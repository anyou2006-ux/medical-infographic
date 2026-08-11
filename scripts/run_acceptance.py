#!/usr/bin/env python3
"""Run the deterministic nine-case acceptance suite."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "medical-infographic"
SKILL_SCRIPTS = SKILL_ROOT / "scripts"
THEMES = SKILL_ROOT / "assets" / "themes"


def load_module(name: str) -> ModuleType:
    path = SKILL_SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"acceptance_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def combined_validation(spec: dict[str, Any], validator: ModuleType) -> dict[str, Any]:
    result = validator.validate_spec(spec)
    if result["status"] == "blocked":
        return result
    content = validator.spec_text(spec)
    content_result = validator.validate_content(
        content,
        spec.get("evidence_mode", "balanced"),
        spec.get("sources", []),
    )
    result["errors"].extend(content_result["errors"])
    result["warnings"].extend(content_result["warnings"])
    result["status"] = "blocked" if result["errors"] else ("warning" if result["warnings"] else "pass")
    return result


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_suite(cases_path: Path, output_dir: Path) -> dict[str, Any]:
    cases_path = Path(cases_path).resolve()
    output_dir = Path(output_dir).resolve()
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    validator = load_module("validate_content")
    renderer = load_module("render_svg")
    checker = load_module("check_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for case in cases:
        case_dir = output_dir / case["id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        spec_path = ROOT / case["fixture"]
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        content_report = combined_validation(spec, validator)
        write_json(case_dir / "content-report.json", content_report)

        svg_paths: list[Path] = []
        if content_report["status"] != "blocked":
            svg_paths = renderer.render_infographic(spec, case_dir, THEMES)
        quality_report = checker.check_outputs(spec, svg_paths, content_report)
        write_json(case_dir / "quality-report.json", quality_report)

        actual = quality_report["status"]
        expected = case["expected"]["status"]
        results.append(
            {
                "id": case["id"],
                "invocation": case["invocation"],
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
                "svg_files": len(svg_paths),
            }
        )

    passed = sum(1 for result in results if result["passed"])
    summary = {
        "status": "pass" if passed == len(results) else "failed",
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 medical-infographic 的九案例验收。")
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "acceptance-cases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "acceptance")
    args = parser.parse_args()
    summary = run_suite(args.cases, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
