#!/usr/bin/env python3
"""Render a deterministic, editable SVG infographic from a JSON spec."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any


CHANNELS = {
    "wechat-long": (1080, 6000),
    "xhs-cards": (1080, 1440),
    "presentation": (1920, 1080),
}
FONT_STACK = "'Noto Sans CJK SC','Microsoft YaHei','PingFang SC',sans-serif"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def wrap_text(text: str, limit: int) -> list[str]:
    text = str(text).strip()
    if not text:
        return []
    return [text[index : index + limit] for index in range(0, len(text), limit)]


def load_theme(theme_name: str, theme_dir: Path) -> dict[str, str]:
    path = theme_dir / f"{theme_name}.json"
    if not path.exists():
        path = theme_dir / "medical-blue.json"
    return json.loads(path.read_text(encoding="utf-8"))


def svg_text(x: int, y: int, value: str, size: int, color: str, weight: int = 400, anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{esc(color)}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" font-family="{FONT_STACK}">{esc(value)}</text>'
    )


def _card(x: int, y: int, width: int, height: int, title: str, items: list[Any], theme: dict[str, str], compact: bool = False) -> str:
    title_size = 28 if compact else 34
    body_size = 22 if compact else 26
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24" fill="{esc(theme["surface"])}" stroke="{esc(theme["border"])}" stroke-width="2"/>',
        svg_text(x + 28, y + 52, title, title_size, theme["accent"], 700),
    ]
    cursor = y + 94
    max_items = max(1, (height - 110) // (body_size + 20))
    for item in items[:max_items]:
        parts.append(f'<circle cx="{x + 35}" cy="{cursor - 7}" r="5" fill="{esc(theme["highlight"])}"/>')
        for line in wrap_text(str(item), max(8, int(width / (body_size * 1.05))))[:2]:
            parts.append(svg_text(x + 54, cursor, line, body_size, theme["text"]))
            cursor += body_size + 8
        cursor += 10
    return "".join(parts)


def _layout_cards(sections: list[dict[str, Any]], width: int, start_y: int, available_h: int, theme: dict[str, str], layout: str) -> str:
    if not sections:
        return svg_text(width // 2, start_y + 120, "未提供内容模块", 34, theme["muted"], anchor="middle")

    margin = 72 if width <= 1080 else 110
    gap = 28
    if layout in {"workflow", "timeline"}:
        card_w = width - margin * 2
        card_h = max(160, min(260, (available_h - gap * (len(sections) - 1)) // max(1, len(sections))))
        parts: list[str] = []
        y = start_y
        for index, section in enumerate(sections):
            sequence = int(section.get("_sequence", index + 1))
            parts.append(_card(margin, y, card_w, card_h, f"{sequence:02d}  {section.get('title', '')}", section.get("items", []), theme, compact=width <= 1080))
            if index < len(sections) - 1:
                cx = width // 2
                parts.append(f'<path d="M {cx} {y + card_h} L {cx} {y + card_h + gap - 8}" stroke="{esc(theme["highlight"])}" stroke-width="5"/>')
                parts.append(f'<path d="M {cx - 9} {y + card_h + gap - 18} L {cx} {y + card_h + gap - 6} L {cx + 9} {y + card_h + gap - 18}" fill="none" stroke="{esc(theme["highlight"])}" stroke-width="4"/>')
            y += card_h + gap
        return "".join(parts)

    if layout == "anatomy" and len(sections) >= 2:
        cx, cy = width // 2, start_y + available_h // 2
        radius = min(width, available_h) // 6
        parts = [f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{esc(theme["accent"])}" opacity="0.22" stroke="{esc(theme["accent"])}" stroke-width="4"/>', svg_text(cx, cy + 10, sections[0].get("title", "核心"), 34, theme["text"], 700, "middle")]
        satellites = sections[1:7]
        card_w = min(340, int(width * 0.3))
        card_h = 190
        orbit = min(width * 0.34, available_h * 0.32)
        for index, section in enumerate(satellites):
            angle = (2 * math.pi * index / max(1, len(satellites))) - math.pi / 2
            sx = int(cx + math.cos(angle) * orbit - card_w / 2)
            sy = int(cy + math.sin(angle) * orbit - card_h / 2)
            parts.append(f'<line x1="{cx}" y1="{cy}" x2="{sx + card_w // 2}" y2="{sy + card_h // 2}" stroke="{esc(theme["border"])}" stroke-width="3"/>')
            parts.append(_card(sx, sy, card_w, card_h, section.get("title", ""), section.get("items", []), theme, compact=True))
        return "".join(parts)

    is_long = available_h > 3000
    columns = 1 if is_long else (2 if width <= 1080 else 3)
    if layout == "matrix":
        columns = 2 if width <= 1080 else 4
    if layout == "dashboard":
        columns = 2 if width <= 1080 else 3
    card_w = (width - margin * 2 - gap * (columns - 1)) // columns
    rows = math.ceil(len(sections) / columns)
    max_card_h = 720 if is_long else 360
    card_h = max(180, min(max_card_h, (available_h - gap * max(0, rows - 1)) // max(1, rows)))
    if is_long and rows > 1:
        gap = min(160, max(gap, (available_h - card_h * rows) // (rows - 1)))
    parts = []
    for index, section in enumerate(sections):
        row, col = divmod(index, columns)
        x = margin + col * (card_w + gap)
        y = start_y + row * (card_h + gap)
        parts.append(_card(x, y, card_w, card_h, section.get("title", ""), section.get("items", []), theme, compact=width <= 1080 and not is_long))
        if layout == "architecture" and index and col > 0:
            parts.append(f'<line x1="{x - gap + 5}" y1="{y + card_h // 2}" x2="{x - 5}" y2="{y + card_h // 2}" stroke="{esc(theme["highlight"])}" stroke-width="4"/>')
    return "".join(parts)


def _page_svg(spec: dict[str, Any], width: int, height: int, theme: dict[str, str], page_index: int, page_count: int, sections: list[dict[str, Any]]) -> str:
    title_limit = 18 if width <= 1080 else 30
    title_lines = wrap_text(spec.get("title", "未命名信息图"), title_limit)[:2]
    subtitle = str(spec.get("subtitle", "")).strip()
    top = 104 if width <= 1080 else 84
    title_size = 56 if width <= 1080 else 64
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{esc(theme["background"])}"/>',
        f'<circle cx="{int(width * .88)}" cy="{int(height * .08)}" r="{int(width * .18)}" fill="{esc(theme["accent"])}" opacity="0.08"/>',
    ]
    if spec.get("visual_asset"):
        asset = Path(str(spec["visual_asset"])).resolve().as_uri()
        parts.append(f'<image href="{esc(asset)}" x="0" y="0" width="{width}" height="{height}" opacity="0.16" preserveAspectRatio="xMidYMid slice"/>')
    y = top
    for line in title_lines:
        parts.append(svg_text(72 if width <= 1080 else 110, y, line, title_size, theme["text"], 800))
        y += title_size + 16
    if subtitle:
        parts.append(svg_text(72 if width <= 1080 else 110, y + 12, subtitle, 28 if width <= 1080 else 30, theme["muted"]))
        y += 62
    parts.append(f'<rect x="{72 if width <= 1080 else 110}" y="{y + 12}" width="160" height="8" rx="4" fill="{esc(theme["highlight"])}"/>')
    content_y = y + 74
    footer_h = 150 if height > 2000 else 92
    content_h = height - content_y - footer_h - 48
    layout = spec.get("layout", "architecture")
    if layout == "auto":
        layout = "architecture"
    parts.append(_layout_cards(sections, width, content_y, content_h, theme, layout))

    sources = spec.get("sources", [])
    source_text = "；".join(str(item.get("title", "")) for item in sources[:3] if item.get("title")) or "来源：未提供"
    parts.append(svg_text(72 if width <= 1080 else 110, height - 56, f"来源：{source_text}" if not source_text.startswith("来源") else source_text, 18 if width <= 1080 else 20, theme["muted"]))
    parts.append(svg_text(width - (72 if width <= 1080 else 110), height - 56, f"{page_index}/{page_count}", 20, theme["muted"], anchor="end"))
    parts.append("</svg>")
    return "".join(parts)


def _split_sections(sections: list[dict[str, Any]], page_count: int, channel: str) -> list[list[dict[str, Any]]]:
    if page_count <= 1:
        return [sections]
    chunks: list[list[dict[str, Any]]] = [[] for _ in range(page_count)]
    if channel == "xhs-cards":
        # Keep the first card concise and reserve the final card for summary/source content.
        chunks[0] = sections[:1]
        remaining = sections[1:]
        for index, section in enumerate(remaining):
            target = 1 + (index % max(1, page_count - 1))
            chunks[target].append(section)
    else:
        for index, section in enumerate(sections):
            chunks[index % page_count].append(section)
    return chunks


def render_infographic(spec: dict[str, Any], output_dir: Path, theme_dir: Path) -> list[Path]:
    channel = spec.get("channel", "presentation")
    if channel not in CHANNELS:
        raise ValueError(f"Unsupported channel: {channel}")
    width, height = CHANNELS[channel]
    pages = spec.get("pages", "auto")
    if pages == "auto":
        pages = 6 if channel == "xhs-cards" else 1
    pages = int(pages)
    if not 1 <= pages <= 10:
        raise ValueError("pages must be between 1 and 10")
    theme = load_theme(spec.get("theme", "medical-blue"), theme_dir)
    sections = [dict(section, _sequence=index) for index, section in enumerate(spec.get("sections", []), start=1)]
    chunks = _split_sections(sections, pages, channel)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, chunk in enumerate(chunks, start=1):
        svg = _page_svg(spec, width, height, theme, index, pages, chunk)
        path = output_dir / f"page-{index:02d}.svg"
        path.write_text(svg, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Render infographic SVG files.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--theme-dir", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "themes")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    paths = render_infographic(spec, args.output_dir, args.theme_dir)
    print(json.dumps({"files": [str(path) for path in paths]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
