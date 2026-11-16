#!/usr/bin/env python3
"""Tukar authorization code YouTube (jalur manual) jadi token.json.

Dipakai kalau redirect ke localhost gagal: setelah tap Allow, browser mungkin
menampilkan "site can't be reached" — salin URL di address bar (ada `code=...`)
lalu jalankan:

  python3 tools/youtube_auth_code.py --url "http://localhost:8765/?code=4/0Ab..."
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "production" / "credentials.json"
TOKEN = ROOT / "production" / "token.json"
REDIRECT = "http://127.0.0.1:8790"
SCOPE = "https://www.googleapis.com/auth/youtube"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL lengkap hasil redirect")
    ap.add_argument("--code", help="code saja")
    args = ap.parse_args()

    code = args.code
    if not code and args.url:
        q = urllib.parse.urlparse(args.url).query or args.url.split("?", 1)[-1]
        code = (urllib.parse.parse_qs(q).get("code") or [""])[0]
    if not code:
        print("code tidak ditemukan")
        return 1

    data = json.loads(CRED.read_text())
    cred = data["youtube"]
    body = urllib.parse.urlencode({
        "code": code, "client_id": cred["client_id"], "client_secret": cred["client_secret"],
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if "refresh_token" not in out:
        print("tidak dapat refresh_token:", out)
        return 1

    TOKEN.write_text(json.dumps({
        "token": out["access_token"], "refresh_token": out["refresh_token"],
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": cred["client_id"], "client_secret": cred["client_secret"],
        "scopes": [SCOPE], "universe_domain": "googleapis.com", "account": "",
    }, indent=2))
    cred["refresh_token"] = out["refresh_token"]
    data["youtube"] = cred
    CRED.write_text(json.dumps(data, indent=2))
    print("OK: token dengan scope youtube tersimpan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
