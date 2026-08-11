#!/usr/bin/env python3
"""Create a machine-readable quality report for rendered SVG output."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


EXPECTED = {
    "wechat-long": (1080, 6000),
    "xhs-cards": (1080, 1440),
    "presentation": (1920, 1080),
}


def check_outputs(spec: dict[str, Any], svg_paths: Iterable[Path], content_result: dict[str, Any]) -> dict[str, Any]:
    paths = [Path(path) for path in svg_paths]
    errors: list[str] = []
    warnings: list[str] = []
    privacy_checked = content_result.get("status") != "blocked"
    layout_checked = True
    channel = spec.get("channel")
    expected = EXPECTED.get(channel)

    if not privacy_checked:
        errors.append("内容验证未通过，输出包含隐私或其他阻断问题。")
    if not paths:
        errors.append("没有可检查的 SVG 文件。")
        layout_checked = False

    for path in paths:
        if not path.exists():
            errors.append(f"输出文件不存在：{path}")
            layout_checked = False
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"SVG 无法解析：{path.name}: {exc}")
            layout_checked = False
            continue
        if expected and (int(root.attrib.get("width", 0)), int(root.attrib.get("height", 0))) != expected:
            errors.append(f"{path.name} 的画布尺寸与渠道不一致。")
            layout_checked = False
        raw = path.read_text(encoding="utf-8")
        if re.search(r"data-overflow=[\"']true[\"']", raw):
            errors.append(f"{path.name} 存在文字溢出标记。")
            layout_checked = False

    sources = spec.get("sources", [])
    if not sources:
        warnings.append("未提供来源；输出只能作为预览版。")

    errors.extend(content_result.get("errors", []))
    warnings.extend(content_result.get("warnings", []))
    status = "blocked" if errors else ("warning" if warnings else "pass")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "evidence_checked": bool(sources),
        "privacy_checked": privacy_checked,
        "layout_checked": layout_checked,
        "render_mode": "hybrid" if spec.get("visual_asset") else "svg",
        "files_checked": len(paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check rendered infographic output.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("svg", nargs="+", type=Path)
    parser.add_argument("--content-report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    content = {"status": "pass", "errors": [], "warnings": []}
    if args.content_report:
        content = json.loads(args.content_report.read_text(encoding="utf-8"))
    report = check_outputs(spec, args.svg, content)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())

