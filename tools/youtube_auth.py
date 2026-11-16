#!/usr/bin/env python3
"""OAuth ulang YouTube dengan scope penuh (`youtube`) supaya bisa hapus/ubah video.

Alur: buka URL izin di browser HP, tap Allow, code ditangkap otomatis oleh
server lokal (http://localhost:8765) lalu token.json ditulis ulang.

  python3 tools/youtube_auth.py
"""
from __future__ import annotations

import http.server
import json
import socket
import socketserver
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "production" / "credentials.json"
TOKEN = ROOT / "production" / "token.json"
PORT = 8790
SCOPE = "https://www.googleapis.com/auth/youtube"
REDIRECT = f"http://127.0.0.1:{PORT}"  # 127.0.0.1: paksa IPv4, hindari ::1

code_holder: dict[str, str] = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        if "code" in params:
            code_holder["code"] = params["code"][0]
            msg = b"<h2>BOCA: izin diterima. Tutup tab ini.</h2>"
        else:
            msg = b"<h2>BOCA: tidak ada code.</h2>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, *a):  # senyap
        pass


def main() -> int:
    cred = json.loads(CRED.read_text())["youtube"]
    cid, secret = cred["client_id"], cred["client_secret"]
    url = ("https://accounts.google.com/o/oauth2/v2/auth?"
           + urllib.parse.urlencode({
               "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
               "scope": SCOPE, "access_type": "offline", "prompt": "consent",
               "include_granted_scopes": "true"}))
    print("URL izin:\n" + url + "\n", flush=True)

    # Dual-stack: Chrome di Android sering resolve "localhost" ke ::1 (IPv6).
    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    srv = Server(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    import subprocess
    subprocess.run(["am", "start", "--user", "0", "-a", "android.intent.action.VIEW",
                    "-d", url], capture_output=True)

    print(f"menunggu izin (maks 300s) di {REDIRECT} ...", flush=True)
    for _ in range(300):
        if "code" in code_holder:
            break
        threading.Event().wait(1)
    srv.shutdown()
    if "code" not in code_holder:
        print("TIMEOUT: tidak ada code diterima")
        return 1

    body = urllib.parse.urlencode({
        "code": code_holder["code"], "client_id": cid, "client_secret": secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if "refresh_token" not in out:
        print("tidak dapat refresh_token:", out)
        return 1

    tok = {"token": out["access_token"], "refresh_token": out["refresh_token"],
           "token_uri": "https://oauth2.googleapis.com/token",
           "client_id": cid, "client_secret": secret, "scopes": [SCOPE],
           "universe_domain": "googleapis.com", "account": ""}
    TOKEN.write_text(json.dumps(tok, indent=2))
    cred["refresh_token"] = out["refresh_token"]
    data = json.loads(CRED.read_text())
    data["youtube"] = cred
    CRED.write_text(json.dumps(data, indent=2))
    print("OK: token.json + credentials.json diperbarui (scope: youtube)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
