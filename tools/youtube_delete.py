#!/usr/bin/env python3
"""Hapus (atau jadikan private) satu video YouTube milik channel sendiri.

Contoh:
  python3 tools/youtube_delete.py --id 3J0ZFVrNe5c
  python3 tools/youtube_delete.py --id 3J0ZFVrNe5c --private   # kalau scope tak izinkan delete
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from publish import http, load_credentials, youtube_token  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="video id YouTube")
    ap.add_argument("--private", action="store_true", help="jadikan private, jangan hapus")
    args = ap.parse_args()

    cred = load_credentials().get("youtube") or {}
    token = youtube_token(cred)
    headers = {"Authorization": f"Bearer {token}"}

    if args.private:
        body = json.dumps({"id": args.id, "status": {"privacyStatus": "private"}}).encode()
        out = http("PUT", "https://www.googleapis.com/youtube/v3/videos?part=status",
                   headers={**headers, "Content-Type": "application/json"}, data=body)
        print("private ok:", json.dumps(out.get("status", out), ensure_ascii=False))
        return 0

    try:
        http("DELETE", f"https://www.googleapis.com/youtube/v3/videos?id={args.id}", headers=headers)
        print(f"deleted: {args.id}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"DELETE gagal: {e}")
        print("coba: python3 tools/youtube_delete.py --id", args.id, "--private")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
