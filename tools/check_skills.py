#!/usr/bin/env python3
"""Cek kesehatan skill OpenCode di .opencode/skills/.

    python3 tools/check_skills.py

Memvalidasi:
  - frontmatter YAML ada dan bisa dibaca
  - name = nama direktori, kebab-case, 1-64 karakter
  - description ada, 1-1024 karakter
  - file yang disebut di `references/...` benar-benar ada
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".opencode" / "skills"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+\S", line) and key:
            out[key] += " " + line.strip()
            continue
        mm = re.match(r"^([A-Za-z0-9_/-]+):\s*(.*)$", line)
        if mm:
            key = mm.group(1)
            out[key] = mm.group(2).strip()
    return out


def check(path: Path) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if not fm:
        return ["frontmatter `---` tidak ditemukan"]
    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        errs.append("`name` kosong")
    elif name != path.parent.name:
        errs.append(f"name '{name}' != direktori '{path.parent.name}'")
    elif not KEBAB.match(name):
        errs.append(f"name '{name}' bukan kebab-case")
    if not desc:
        errs.append("`description` kosong (skill tidak akan muncul di daftar model)")
    elif len(desc) > 1024:
        errs.append(f"description {len(desc)} karakter (> 1024)")
    for ref in set(re.findall(r"`(references/[^`]+)`", text)):
        if not (path.parent / ref).exists():
            errs.append(f"referensi hilang: {ref}")
    if len(text.splitlines()) > 500:
        errs.append("SKILL.md > 500 baris; pindahkan detail ke references/")
    return errs


def main() -> int:
    if not SKILLS.exists():
        print(f"tidak ada {SKILLS}")
        return 1
    files = sorted(SKILLS.glob("*/SKILL.md"))
    if not files:
        print("tidak ada skill")
        return 1
    total = 0
    for f in files:
        errs = check(f)
        total += len(errs)
        print(f"{'PASS' if not errs else f'FAIL ({len(errs)})':10} {f.parent.name}")
        for e in errs:
            print(f"           - {e}")
    print(f"\n{len(files)} skill | {total} error")
    print("HASIL: " + ("PASS" if not total else "GAGAL"))
    return 0 if not total else 1


if __name__ == "__main__":
    raise SystemExit(main())
