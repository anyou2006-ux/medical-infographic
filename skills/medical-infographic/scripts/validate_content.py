#!/usr/bin/env python3
"""Validate infographic inputs without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CHANNELS = {"wechat-long", "xhs-cards", "presentation"}
LAYOUTS = {"auto", "architecture", "workflow", "timeline", "matrix", "dashboard", "anatomy"}
DENSITIES = {"standard", "high"}
THEMES = {"medical-blue", "clinical-green", "dark-tech", "custom"}
EVIDENCE_MODES = {"strict", "balanced", "source-only"}
RENDER_MODES = {"gpt-only", "hybrid", "svg"}

PRIVACY_PATTERNS = {
    "患者姓名": re.compile(r"(?:患者姓名|姓名)\s*[：:]\s*[\u4e00-\u9fff·]{2,8}"),
    "身份证号": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "病历号": re.compile(r"(?:病历号|住院号|门诊号)\s*[：:]?\s*[A-Za-z0-9-]{4,}"),
}

HIGH_RISK = re.compile(
    r"TOP\s*\d+|排名|市场份额|投融资|融资额|审批周期|工作日|"
    r"临床效果|准确率|敏感度|特异度|政策条款|法规要求|设备参数|"
    r"同比|亿元|万美元|回本点|ROI",
    re.IGNORECASE,
)
ILLUSTRATIVE = re.compile(r"示意数据|示例数据|仅用于(?:版式|演示)|虚构数据")


def spec_text(spec: dict[str, Any]) -> str:
    """Collect all human-visible spec text for privacy and evidence checks."""
    values = [str(spec.get("title", "")), str(spec.get("subtitle", ""))]
    for section in spec.get("sections", []):
        if not isinstance(section, dict):
            continue
        values.append(str(section.get("layer", "")))
        values.append(str(section.get("title", "")))
        values.extend(str(item) for item in section.get("items", []) if item is not None)
    return "\n".join(value for value in values if value.strip())


def _result(errors: list[str], warnings: list[str], normalized: dict[str, Any] | None = None) -> dict[str, Any]:
    status = "blocked" if errors else ("warning" if warnings else "pass")
    result: dict[str, Any] = {"status": status, "errors": errors, "warnings": warnings}
    if normalized is not None:
        result["normalized"] = normalized
    return result


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized = dict(spec)

    if not isinstance(spec.get("title"), str) or not spec.get("title", "").strip():
        errors.append("title 必须是非空字符串。")

    channel = spec.get("channel")
    if channel not in CHANNELS:
        errors.append(f"channel 必须是以下值之一：{', '.join(sorted(CHANNELS))}。")

    normalized.setdefault("layout", "auto")
    normalized.setdefault("render_mode", "gpt-only")
    normalized.setdefault("density", "standard")
    normalized.setdefault("theme", "medical-blue")
    normalized.setdefault("evidence_mode", "balanced")
    normalized.setdefault("language", "zh-CN")
    normalized.setdefault("pages", "auto")
    normalized.setdefault("sections", [])
    normalized.setdefault("sources", [])

    if normalized["layout"] not in LAYOUTS:
        errors.append(f"layout 不受支持：{normalized['layout']}。")
    if normalized["render_mode"] not in RENDER_MODES:
        errors.append(f"render_mode 不受支持：{normalized['render_mode']}。")
    if normalized["density"] not in DENSITIES:
        errors.append(f"density 不受支持：{normalized['density']}。")
    if normalized["theme"] not in THEMES:
        errors.append(f"theme 不受支持：{normalized['theme']}。")
    if normalized["evidence_mode"] not in EVIDENCE_MODES:
        errors.append(f"evidence_mode 不受支持：{normalized['evidence_mode']}。")
    if normalized["language"] != "zh-CN":
        errors.append("首版仅支持 language: zh-CN。")

    pages = normalized["pages"]
    if pages != "auto" and (not isinstance(pages, int) or isinstance(pages, bool) or not 1 <= pages <= 10):
        errors.append("pages 必须是 auto 或 1—10 的整数。")

    if not isinstance(normalized["sections"], list):
        errors.append("sections 必须是数组。")
    else:
        for index, section in enumerate(normalized["sections"], start=1):
            if not isinstance(section, dict) or not str(section.get("title", "")).strip():
                errors.append(f"sections[{index}] 缺少标题。")
            if isinstance(section, dict) and "layer" in section and not isinstance(section.get("layer"), str):
                errors.append(f"sections[{index}].layer 必须是字符串。")
            if not isinstance(section.get("items", []), list):
                errors.append(f"sections[{index}].items 必须是数组。")

    if not isinstance(normalized["sources"], list):
        errors.append("sources 必须是数组。")

    if channel == "xhs-cards" and pages == 1:
        warnings.append("小红书单页模式可能承载过多内容。")

    return _result(errors, warnings, normalized)


def validate_content(text: str, evidence_mode: str = "balanced", sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    sources = sources or []

    privacy_hits = [name for name, pattern in PRIVACY_PATTERNS.items() if pattern.search(text)]
    if privacy_hits:
        errors.append(f"检测到患者隐私信息：{', '.join(privacy_hits)}。请匿名化后重试。")

    high_risk = bool(HIGH_RISK.search(text))
    illustrative = bool(ILLUSTRATIVE.search(text))
    if high_risk and not sources and not illustrative:
        if evidence_mode in {"strict", "balanced"}:
            errors.append("高风险事实缺少来源，不能生成最终版。")
        elif evidence_mode == "source-only":
            warnings.append("内容包含高风险事实但未提供来源；仅可生成未经外部核验的预览版。")

    if evidence_mode not in EVIDENCE_MODES:
        errors.append("evidence_mode 参数无效。")
    if illustrative:
        warnings.append("检测到示意数据，成图必须保留示意标记。")

    return _result(errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate medical infographic content and spec.")
    parser.add_argument("--spec", type=Path, help="Path to infographic spec JSON.")
    parser.add_argument("--text", help="Content text to validate.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    if args.spec:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        result = validate_spec(spec)
        if result["status"] != "blocked":
            content = args.text or spec_text(spec)
            content_result = validate_content(content, spec.get("evidence_mode", "balanced"), spec.get("sources", []))
            result["errors"].extend(content_result["errors"])
            result["warnings"].extend(content_result["warnings"])
            result["status"] = "blocked" if result["errors"] else ("warning" if result["warnings"] else "pass")
    else:
        result = validate_content(args.text or "")

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())

