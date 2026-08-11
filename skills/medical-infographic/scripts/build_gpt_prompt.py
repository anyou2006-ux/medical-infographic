#!/usr/bin/env python3
"""Build reproducible page prompts for GPT-first infographic rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CHANNELS = {
    "wechat-long": (1080, 6000, "微信公众号竖版长图"),
    "xhs-cards": (1080, 1440, "小红书 3:4 卡片"),
    "presentation": (1920, 1080, "电脑与 PPT 16:9 横版"),
}

LAYOUT_GUIDE = {
    "architecture": "按清晰层级组织模块，连接线和箭头方向明确",
    "workflow": "按连续步骤组织，从起点到终点保持单一阅读方向",
    "timeline": "按时间顺序组织节点，时间口径一致",
    "matrix": "按行列对齐比较维度，表头与单元格边界清晰",
    "dashboard": "按指标层级组织卡片，只显示提供的真实或明确示意数据",
    "anatomy": "以核心对象为中心，外围能力用引线对应到正确位置",
    "auto": "根据内容自动选择最清晰的信息结构",
}

THEMES = {
    "medical-blue": "医疗蓝与深海军蓝，青色强调，专业、可信、现代",
    "clinical-green": "临床绿色与柔和青色，洁净、克制、可信",
    "dark-tech": "深色科技底，蓝紫与青色微光，高对比但不炫目",
    "custom": "严格遵循用户提供的自定义视觉要求",
}


def page_count(spec: dict[str, Any]) -> int:
    pages = spec.get("pages", "auto")
    if isinstance(pages, int):
        return pages
    return 6 if spec.get("channel") == "xhs-cards" else 1


def split_sections(sections: list[dict[str, Any]], pages: int, channel: str) -> list[list[dict[str, Any]]]:
    if pages <= 1:
        return [sections]
    chunks: list[list[dict[str, Any]]] = [[] for _ in range(pages)]
    if channel == "xhs-cards":
        chunks[0] = sections[:1]
        for index, section in enumerate(sections[1:]):
            chunks[1 + index % max(1, pages - 1)].append(section)
    else:
        for index, section in enumerate(sections):
            chunks[index % pages].append(section)
    return chunks


def visible_text(spec: dict[str, Any], sections: list[dict[str, Any]], page_index: int, pages: int) -> str:
    lines = [f'主标题："{spec["title"]}"']
    subtitle = str(spec.get("subtitle", "")).strip()
    if subtitle:
        lines.append(f'副标题："{subtitle}"')
    emitted_layers: set[str] = set()
    for section in sections:
        layer = str(section.get("layer", "")).strip()
        if layer and layer not in emitted_layers:
            lines.append(f'层级标签："{layer}"')
            emitted_layers.add(layer)
        lines.append(f'模块标题："{section.get("title", "")}"')
        for item in section.get("items", []):
            lines.append(f'  - "{item}"')
    sources = [str(item.get("title", "")).strip() for item in spec.get("sources", []) if item.get("title")]
    if sources:
        lines.append(f'来源："{"；".join(sources[:3])}"')
    if pages > 1:
        lines.append(f'页码："{page_index}/{pages}"')
    return "\n".join(lines)


def structure_instruction(layout: str, channel: str, sections: list[dict[str, Any]]) -> str:
    module_count = len(sections)
    if layout != "architecture":
        return f"本页包含 {module_count} 个主要信息模块。"

    layer_counts: dict[str, int] = {}
    for section in sections:
        layer = str(section.get("layer", "")).strip()
        if layer:
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

    if layer_counts:
        summary = "；".join(f"{layer}：{count} 个模块" for layer, count in layer_counts.items())
        grid = ""
        if channel == "presentation":
            columns = max(layer_counts.values())
            grid = f" 横版主体按 {len(layer_counts)} 行 × {columns} 列网格排列；层级标签位于每行左侧。"
        return (
            f"本页为分层架构，共 {len(layer_counts)} 个层级、{module_count} 个模块。{summary}。"
            f"{grid} 使用对齐的双向细箭头表达数据上行与业务反馈，不让连线穿过文字。"
        )

    if channel == "presentation" and module_count == 9:
        return "本页包含 9 个模块，横版主体采用 3 行 × 3 列规则网格；连接线置于卡片之间。"
    return f"本页包含 {module_count} 个架构模块，按清晰层级排列，连接线不得穿过文字。"


def build_prompt(spec: dict[str, Any], sections: list[dict[str, Any]], page_index: int, pages: int) -> str:
    channel = spec.get("channel", "presentation")
    width, height, channel_label = CHANNELS[channel]
    layout = spec.get("layout", "auto")
    density = spec.get("density", "standard")
    theme = spec.get("theme", "medical-blue")
    density_rule = (
        "高密度编辑型信息图；文字多但必须清晰，优先减少装饰与留白，绝不遗漏正文。"
        if density == "high"
        else "标准信息密度；保持充足留白与清晰层级。"
    )
    text_block = visible_text(spec, sections, page_index, pages)
    structure = structure_instruction(layout, channel, sections)
    return f"""Use case: infographic-diagram
Asset type: {channel_label}医疗信息化信息图，第 {page_index}/{pages} 页
Canvas: {width} × {height}，严格保持对应比例，整页成图，不要放在设备或纸张样机中
Primary request: 根据以下锁定内容，直接生成一张完成度高的中文医疗信息化信息图
Layout: {layout}；{LAYOUT_GUIDE.get(layout, LAYOUT_GUIDE['auto'])}
Structure: {structure}
Density: {density_rule}
Visual style: {THEMES.get(theme, THEMES['medical-blue'])}；专业医疗科技编辑设计；结构清楚；适合屏幕与投影阅读

可见文字清单（逐字照抄）：
{text_block}

文字硬性规则：
1. 只使用上方清单中的文字，逐字照抄，每条只出现一次；不得翻译、改写、增删或补充占位文字。
2. 中文是主要信息，不得出现乱码、同音错字、伪字、重复字；英文缩写、数字、单位和日期保持原样。
3. 标题、模块、正文、来源和页码层级明确；正文必须可读，不能用极小字号挤压。
4. 如果空间不足，减少装饰、图标和留白；不得省略文字。

构图规则：
1. 信息层在前，装饰在后；严格遵循 Structure 指定的层数、模块数、网格与层级标签；模块边界、连接方向与阅读顺序清楚。
2. 使用统一卡片、细线图标和克制的医疗科技纹理，不使用真实病历界面或可识别患者画面。
3. 保持安全边距，不裁切标题、正文、来源或页码。
4. 输出最终信息图本身，不要解释设计，不要生成多个方案。

Avoid: 水印、Logo、品牌名、清单外文字、随机数字、虚构指标、乱码、装饰性英文、伪造软件截图、拥挤背景、低对比度正文
"""


def write_prompts(spec: dict[str, Any], output_dir: Path) -> list[Path]:
    pages = page_count(spec)
    chunks = split_sections(spec.get("sections", []), pages, spec.get("channel", "presentation"))
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, chunk in enumerate(chunks, start=1):
        path = output_dir / f"gpt-prompt-{index:02d}.txt"
        path.write_text(build_prompt(spec, chunk, index, pages), encoding="utf-8")
        paths.append(path)
    manifest = {
        "render_mode": spec.get("render_mode", "gpt-only"),
        "channel": spec.get("channel"),
        "pages": pages,
        "layers": list(dict.fromkeys(
            str(section.get("layer", "")).strip()
            for section in spec.get("sections", [])
            if str(section.get("layer", "")).strip()
        )),
        "prompts": [path.name for path in paths],
    }
    (output_dir / "gpt-prompt-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Build page prompts for GPT infographic rendering.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    paths = write_prompts(spec, args.output_dir)
    print(json.dumps({"files": [str(path) for path in paths]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
