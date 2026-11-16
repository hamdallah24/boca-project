#!/usr/bin/env python3
"""Fetch anti-copyright (public domain / CC0 only) background photos for BOCA animatics.

Source: Wikimedia Commons API. Every file is checked to be Public Domain or CC0
before download; anything else is rejected so the channel stays copyright-safe.
Credits are written to assets/bg/credits.json + CREDITS.md.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "bg"
OUT.mkdir(parents=True, exist_ok=True)

UA = "BocaAnimatic/1.0 (educational short-form video)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# key -> exact Commons file title (verified public domain / CC0)
TARGETS = {
    "sky_ground": "File:Dunes and beach grass under a blue sky, Province Lands, Provincetown, Massachusetts.jpg",
    "sky_open": "File:Sky Sun Blue Dark Clouds Rays Weather.jpg",
    "prism": "File:Dispersion of White Light Through a Prism.jpg",
    "atmosphere": "File:ISS-59 Sun's first rays peek above Earth's limb.jpg",
    "sunset": "File:Sunset from the ISS.JPG",
    "space_earth": "File:The Earth seen from Apollo 17.jpg",
    "earthrise": "File:Earthrise.jpg",
}

ALLOWED = ("public domain", "cc0", "pd", "no restrictions")


def http_json(url: str, tries: int = 3) -> dict:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 2)
    raise RuntimeError(f"failed: {url} -> {last!r}")


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&#039;", "'")
    return re.sub(r"\s+", " ", text).strip()


def is_free_license(short: str, long: str) -> bool:
    s = (short or "").lower().strip()
    l = (long or "").lower()
    if s in ALLOWED:
        return True
    if "cc0" in s:
        return True
    if "public domain" in s or "public domain" in l:
        return True
    return False


def fetch_one(key: str, title: str, width: int = 1800) -> dict:
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size",
        "iiurlwidth": str(width),
        "format": "json",
    }
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    data = http_json(url)
    pages = (data.get("query") or {}).get("pages") or {}
    page = next(iter(pages.values()))
    if "missing" in page:
        raise RuntimeError(f"{key}: '{title}' not found")
    info = (page.get("imageinfo") or [{}])[0]
    if not info.get("thumburl"):
        raise RuntimeError(f"{key}: no thumb url for '{title}'")
    meta = info.get("extmetadata") or {}
    lic_short = strip_html((meta.get("LicenseShortName") or {}).get("value", ""))
    lic_long = strip_html((meta.get("License") or {}).get("value", ""))
    if not is_free_license(lic_short, lic_long):
        raise RuntimeError(f"{key}: license '{lic_short}' is not public domain / CC0 - skipped")
    return {
        "key": key,
        "url": info["thumburl"],
        "file": f"{key}.jpg",
        "page": info.get("descriptionurl", ""),
        "title": page.get("title", ""),
        "author": strip_html((meta.get("Artist") or {}).get("value", "")) or "Unknown",
        "credit": strip_html((meta.get("Credit") or {}).get("value", "")),
        "license": lic_short or "Public domain",
        "license_url": (meta.get("LicenseUrl") or {}).get("value", ""),
        "source": "Wikimedia Commons",
        "width": info.get("width"),
        "height": info.get("height"),
    }


def download(rec: dict) -> Path:
    dest = OUT / rec["file"]
    if dest.exists() and dest.stat().st_size > 20000:
        return dest
    req = urllib.request.Request(rec["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        dest.write_bytes(r.read())
    return dest


def main() -> None:
    records: list[dict] = []
    failed: list[str] = []
    for key, title in TARGETS.items():
        try:
            rec = fetch_one(key, title)
            p = download(rec)
            rec["bytes"] = p.stat().st_size
            records.append(rec)
            print(f"ok  {key:12s} {rec['license']:22s} {rec['bytes'] // 1024:5d}KB  {rec['title'][:55]}")
        except Exception as e:  # noqa: BLE001
            failed.append(f"{key}: {e}")
            print(f"ERR {key:12s} {e}")
        time.sleep(0.4)

    (OUT / "credits.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Background credits",
        "",
        "Semua background BOCA memakai gambar **Public Domain / CC0** dari Wikimedia Commons.",
        "Tidak ada foto berbayar, stock, atau aset berlisensi ketat di pipeline ini.",
        "",
        "| File | Judul | Lisensi | Pembuat | Sumber |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(
            f"| `{r['file']}` | {r['title'].replace('File:','')} | {r['license']} | "
            f"{r['author'][:60]} | {r['page']} |"
        )
    lines += ["", "## Catatan", "", "- Public domain: boleh dipakai tanpa Credit (tetap kami cantumkan).",
              "- CC0:-domain-like, bebas dipakai tanpa syarat.", ""]
    (OUT / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote", OUT / "credits.json", "and", OUT / "CREDITS.md")
    if failed:
        print("failures:", failed)


if __name__ == "__main__":
    main()
