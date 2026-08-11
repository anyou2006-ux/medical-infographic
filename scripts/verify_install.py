#!/usr/bin/env python3
"""Verify a user-level installation of the medical infographic skill."""

from __future__ import annotations

import argparse
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
    "scripts/render_svg.py",
    "scripts/render_png.cjs",
    "scripts/check_output.py",
    "references/channels.md",
    "references/layouts.md",
    "references/evidence-policy.md",
    "references/hybrid-rendering.md",
    "references/output-schema.md",
)


def default_install_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / "medical-infographic"


def verify_install(installed: Path) -> dict[str, Any]:
    installed = Path(installed).resolve()
    errors: list[str] = []
    checked = 0
    for relative in REQUIRED_FILES:
        path = installed / relative
        if not path.is_file():
            errors.append(f"缺少文件：{relative}")
            continue
        checked += 1
        if path.stat().st_size == 0:
            errors.append(f"文件为空：{relative}")

    skill_name = None
    skill_md = installed / "SKILL.md"
    if skill_md.is_file():
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", skill_md.read_text(encoding="utf-8"))
        skill_name = match.group(1) if match else None
        if skill_name != "medical-infographic":
            errors.append("SKILL.md 的 name 不是 medical-infographic。")

    return {
        "status": "pass" if not errors else "failed",
        "installed_path": str(installed),
        "skill_name": skill_name,
        "files_checked": checked,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 medical-infographic 的用户级安装。")
    parser.add_argument("--installed", type=Path, default=default_install_path())
    args = parser.parse_args()
    report = verify_install(args.installed)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
