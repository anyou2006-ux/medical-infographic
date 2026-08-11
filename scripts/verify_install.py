#!/usr/bin/env python3
"""Verify a user-level installation of the medical infographic skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "assets/infographic-spec.schema.json",
    "assets/themes/medical-blue.json",
    "assets/themes/clinical-green.json",
    "assets/themes/dark-tech.json",
    "scripts/validate_content.py",
    "scripts/build_gpt_prompt.py",
    "scripts/render_svg.py",
    "scripts/render_png.cjs",
    "scripts/check_output.py",
    "references/channels.md",
    "references/layouts.md",
    "references/evidence-policy.md",
    "references/gpt-rendering.md",
    "references/hybrid-rendering.md",
    "references/output-schema.md",
)


def default_install_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / "medical-infographic"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    digest.update(data)
    return digest.hexdigest()


def verify_install(installed: Path, source: Path | None = None) -> dict[str, Any]:
    installed = Path(installed).resolve()
    source = Path(source).resolve() if source else None
    errors: list[str] = []
    mismatched: list[str] = []
    checked = 0
    for relative in REQUIRED_FILES:
        path = installed / relative
        if not path.is_file():
            errors.append(f"缺少文件：{relative}")
            continue
        checked += 1
        if path.stat().st_size == 0:
            errors.append(f"文件为空：{relative}")
        if source:
            source_file = source / relative
            if not source_file.is_file() or file_hash(path) != file_hash(source_file):
                mismatched.append(relative)

    skill_name = None
    skill_md = installed / "SKILL.md"
    if skill_md.is_file():
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", skill_md.read_text(encoding="utf-8"))
        skill_name = match.group(1) if match else None
        if skill_name != "medical-infographic":
            errors.append("SKILL.md 的 name 不是 medical-infographic。")

    if mismatched:
        errors.append(f"安装内容与指定来源不一致：{', '.join(mismatched)}")

    return {
        "status": "pass" if not errors else "failed",
        "installed_path": str(installed),
        "source_path": str(source) if source else None,
        "source_match": not mismatched if source else None,
        "skill_name": skill_name,
        "files_checked": checked,
        "mismatched_files": mismatched,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 medical-infographic 的用户级安装。")
    parser.add_argument("--installed", type=Path, default=default_install_path())
    parser.add_argument("--source", type=Path, help="可选的来源 Skill 目录，用于 SHA-256 一致性检查。")
    args = parser.parse_args()
    report = verify_install(args.installed, source=args.source)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
