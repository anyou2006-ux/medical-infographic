#!/usr/bin/env python3
"""Create a machine-readable quality report for GPT PNG or SVG fallback output."""

from __future__ import annotations

import argparse
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


EXPECTED = {
    "wechat-long": (1080, 6000),
    "xhs-cards": (1080, 1440),
    "presentation": (1920, 1080),
}


def _png_size(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()[:24]
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise ValueError("不是有效的 PNG 文件")
    return struct.unpack(">II", raw[16:24])


def check_outputs(
    spec: dict[str, Any],
    output_paths: Iterable[Path],
    content_result: dict[str, Any],
    visual_reviewed: bool = False,
) -> dict[str, Any]:
    paths = [Path(path) for path in output_paths]
    errors: list[str] = []
    warnings: list[str] = []
    dimensions: list[dict[str, Any]] = []
    privacy_checked = content_result.get("status") != "blocked"
    layout_checked = True
    channel = spec.get("channel")
    expected = EXPECTED.get(channel)

    if not privacy_checked:
        errors.append("内容验证未通过，输出包含隐私或其他阻断问题。")
    if not paths:
        errors.append("没有可检查的输出文件。")
        layout_checked = False

    for path in paths:
        if not path.exists():
            errors.append(f"输出文件不存在：{path}")
            layout_checked = False
            continue
        suffix = path.suffix.lower()
        if suffix == ".svg":
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError as exc:
                errors.append(f"SVG 无法解析：{path.name}: {exc}")
                layout_checked = False
                continue
            if expected and (int(root.attrib.get("width", 0)), int(root.attrib.get("height", 0))) != expected:
                errors.append(f"{path.name} 的画布尺寸与渠道不一致。")
                layout_checked = False
            dimensions.append(
                {
                    "file": path.name,
                    "width": int(root.attrib.get("width", 0)),
                    "height": int(root.attrib.get("height", 0)),
                }
            )
            raw = path.read_text(encoding="utf-8")
            if re.search(r"data-overflow=[\"']true[\"']", raw):
                errors.append(f"{path.name} 存在文字溢出标记。")
                layout_checked = False
        elif suffix == ".png":
            try:
                width, height = _png_size(path)
            except ValueError as exc:
                errors.append(f"PNG 无法解析：{path.name}: {exc}")
                layout_checked = False
                continue
            dimensions.append({"file": path.name, "width": width, "height": height})
            if expected:
                expected_ratio = expected[0] / expected[1]
                actual_ratio = width / height
                if abs(actual_ratio - expected_ratio) / expected_ratio > 0.02:
                    errors.append(f"{path.name} 的宽高比与渠道不一致。")
                    layout_checked = False
        else:
            errors.append(f"不支持的输出格式：{path.name}")
            layout_checked = False

    requested_mode = spec.get("render_mode", "gpt-only")
    has_png = any(path.suffix.lower() == ".png" for path in paths)
    if requested_mode == "gpt-only" and has_png and not visual_reviewed:
        warnings.append("GPT 直出页面尚未标记为逐字视觉核验完成。")

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
        "render_mode": (
            "gpt-only" if requested_mode == "gpt-only" and has_png
            else "hybrid" if spec.get("visual_asset")
            else "svg-fallback"
        ),
        "visual_reviewed": visual_reviewed,
        "files_checked": len(paths),
        "dimensions": dimensions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check rendered infographic output.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("output_files", nargs="+", type=Path)
    parser.add_argument("--content-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--visual-reviewed", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    content = {"status": "pass", "errors": [], "warnings": []}
    if args.content_report:
        content = json.loads(args.content_report.read_text(encoding="utf-8"))
    report = check_outputs(spec, args.output_files, content, visual_reviewed=args.visual_reviewed)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
