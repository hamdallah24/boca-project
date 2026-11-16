#!/data/data/com.termux/files/usr/bin/python3
"""BOCA auto-publisher untuk 4 platform: YouTube Shorts, IG Reels, FB Reels, TikTok.

Default: DRY-RUN (hanya centricetak langkah + cek kredensial). Upload sungguhan
hanya jalan dengan --publish.

Kredensial dibaca dari:
  1. env (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, IG_USER_ID,
     IG_PAGE_ID, IG_ACCESS_TOKEN, FB_PAGE_ID, FB_ACCESS_TOKEN,
     TT_ACCESS_TOKEN, TT_PRIVACY_LEVEL)
  2. production/credentials.json (jangan di-commit)

Payload per episode: production/payloads/BOCA-DNN.json (dibuat daily_build.py).
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROD = ROOT / "production"
CRED_FILE = PROD / "credentials.json"
LOG_FILE = PROD / "publish_log.json"

GRAPH = "https://graph.facebook.com/v27.0"
RPLOAD_IG = "https://rupload.facebook.com/ig-api-upload/v27.0"
TIKTOK_API = "https://open.tiktokapis.com/v2"
YT_API = "https://www.googleapis.com/upload/youtube/v3"


def load_credentials() -> dict:
    cred = {}
    if CRED_FILE.exists():
        try:
            cred = json.loads(CRED_FILE.read_text(encoding="utf-8"))
        except Exception:
            cred = {}
    env_map = {
        "youtube": {"client_id": "YT_CLIENT_ID", "client_secret": "YT_CLIENT_SECRET",
                    "refresh_token": "YT_REFRESH_TOKEN"},
        "instagram": {"ig_user_id": "IG_USER_ID", "page_id": "IG_PAGE_ID",
                      "access_token": "IG_ACCESS_TOKEN"},
        "facebook": {"page_id": "FB_PAGE_ID", "access_token": "FB_ACCESS_TOKEN"},
        "tiktok": {"access_token": "TT_ACCESS_TOKEN", "privacy_level": "TT_PRIVACY_LEVEL"},
    }
    for plat, keys in env_map.items():
        cred.setdefault(plat, {})
        for field, var in keys.items():
            val = os.environ.get(var)
            if val and not cred[plat].get(field):
                cred[plat][field] = val
    return cred


def http(method: str, url: str, *, headers: dict | None = None, data: bytes | None = None,
         params: dict | None = None, json_body: dict | None = None, timeout: int = 120) -> dict:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    head = dict(headers or {})
    body = data
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        head.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=head, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        hdrs = dict(r.headers)
        try:
            out = json.loads(raw.decode("utf-8"))
            if isinstance(out, dict):
                out["_headers"] = hdrs
            return out
        except Exception:
            return {"_raw": raw[:400].decode("utf-8", "ignore"), "_status": r.status, "_headers": hdrs}


# ------------------------------------------------------------------- YouTube
def youtube_token(cred: dict) -> str:
    """Ambil access token: utamakan token.json (library resmi), fallback refresh_token."""
    token_file = cred.get("token_file")
    if not token_file:
        cand = CRED_FILE.parent / "token.json"
        token_file = str(cand) if cand.exists() else ""
    if token_file and Path(token_file).exists():
        try:
            import importlib.util
            if importlib.util.find_spec("google.oauth2.credentials") is None:
                raise ModuleNotFoundError("google-auth tidak terpasang di interpreter ini")
            from google.oauth2.credentials import Credentials  # type: ignore
            from google.auth.transport.requests import Request  # type: ignore
            c = Credentials.from_authorized_user_file(token_file, ["https://www.googleapis.com/auth/youtube"])
            if not c.valid:
                c.refresh(Request())
                Path(token_file).write_text(c.to_json(), encoding="utf-8")
            return c.token
        except ModuleNotFoundError:
            pass  # diam: lanjut pakai refresh_token
        except Exception as e:  # noqa: BLE001
            print(f"    token.json gagal dipakai ({e}), fallback ke refresh_token")
    body = urllib.parse.urlencode({
        "client_id": cred["client_id"], "client_secret": cred["client_secret"],
        "refresh_token": cred["refresh_token"], "grant_type": "refresh_token",
    }).encode()
    out = http("POST", "https://oauth2.googleapis.com/token", headers={
        "Content-Type": "application/x-www-form-urlencoded"}, data=body)
    return out["access_token"]


def publish_youtube(payload: dict, cred: dict, dry: bool, privacy: str = "public") -> dict:
    has_token = bool(cred.get("refresh_token")) or bool(cred.get("token_file"))
    if not has_token:
        return {"ok": False, "error": "kredensial YouTube belum ada (refresh_token / token.json)"}
    if not (cred.get("client_id") and cred.get("client_secret")) and not cred.get("token_file"):
        return {"ok": False, "error": "kredensial YouTube kurang: client_id/client_secret/refresh_token"}
    video = Path(payload["video_path"])
    if not video.exists():
        return {"ok": False, "error": f"video tidak ada: {video}"}
    title = payload["title"][:95]
    desc = payload.get("description", "")
    tags = payload.get("hashtags", [])
    body = {
        "snippet": {
            "title": title,
            "description": desc[:5000] + "\n\n#Shorts",
            "tags": [t.lstrip("#") for t in tags],
            "categoryId": "27",   # Education
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    print(f"  [youtube] resumable upload: {title}")
    print(f"            category=Education tags={tags} privacy={privacy}")
    if dry:
        return {"ok": True, "dry_run": True, "detail": f"would upload {video.name} ({video.stat().st_size} bytes)"}
    token = youtube_token(cred)
    init = http("POST", f"{YT_API}/videos", params={"uploadType": "resumable", "part": "snippet,status"},
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json; charset=UTF-8",
                         "X-Upload-Content-Type": "video/mp4"},
                json_body=body, timeout=60)
    hdrs = init.get("_headers") or {}
    loc = hdrs.get("Location") or hdrs.get("location") or init.get("location")
    if not loc:
        return {"ok": False, "error": f"gagal inisialisasi upload: {str(init)[:200]}"}
    with open(video, "rb") as fh:
        raw = fh.read()
    res = http("PUT", loc, headers={"Content-Type": "video/mp4",
                                    "Content-Length": str(len(raw))}, data=raw, timeout=900)
    vid = res.get("id") or (res.get("resourceId") if isinstance(res, dict) else None)
    snippet = (res.get("snippet") or {}) if isinstance(res, dict) else {}
    return {"ok": bool(vid), "platform": "youtube_short", "video_id": vid,
            "url": f"https://youtu.be/{vid}" if vid else None,
            "title": snippet.get("title"),
            "status": (res.get("status") or {}) if isinstance(res, dict) else {},
            "raw": str(res)[:160] if not vid else ""}


# ----------------------------------------------------------------- Instagram
def publish_instagram(payload: dict, cred: dict, dry: bool) -> dict:
    """IG Reels - flow resmi v27.0: container (upload_type=resumable) -> upload -> publish."""
    need = ["ig_user_id", "access_token"]
    missing = [k for k in need if not cred.get(k)]
    if missing:
        return {"ok": False, "error": f"kredensial Instagram kurang: {missing}"}
    video = Path(payload["video_path"])
    if not video.exists():
        return {"ok": False, "error": f"video tidak ada: {video}"}
    ig = cred["ig_user_id"]
    token = cred["access_token"]
    caption = payload.get("description", "")[:2200]
    print(f"  [instagram] reels untuk ig_user_id={ig}")
    print(f"              caption={caption[:60]}...")
    if dry:
        return {"ok": True, "dry_run": True, "detail": "would publish reel: container -> rupload -> media_publish"}
    # 1) container + sesi upload resumable
    cont = http("POST", f"{GRAPH}/{ig}/media", params={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "access_token": token})
    container = cont.get("id")
    if not container:
        return {"ok": False, "error": f"gagal bikin container: {str(cont)[:250]}"}
    # 2) transfer file ke rupload.facebook.com
    with open(video, "rb") as fh:
        raw = fh.read()
    up = http("POST", f"{RPLOAD_IG}/{container}", headers={
        "Authorization": f"OAuth {token}", "offset": "0",
        "file_size": str(len(raw)), "Content-Type": "application/octet-stream",
    }, data=raw, timeout=900)
    if not (isinstance(up, dict) and up.get("success")):
        return {"ok": False, "error": f"upload gagal: {str(up)[:250]}"}
    # 3) tunggu container FINISHED
    status = ""
    for _ in range(20):
        time.sleep(5)
        st = http("GET", f"{GRAPH}/{container}", params={
            "fields": "status_code", "access_token": token})
        status = st.get("status_code", "")
        if status in ("FINISHED", "ERROR", "EXPIRED", "PUBLISHED"):
            break
    if status not in ("FINISHED", "PUBLISHED"):
        return {"ok": False, "error": f"container tidak jadi FINISHED (status={status})"}
    # 4) publish
    res = http("POST", f"{GRAPH}/{ig}/media_publish", params={
        "creation_id": container, "access_token": token})
    if "id" not in res:
        return {"ok": False, "error": f"media_publish gagal: {str(res)[:250]}"}
    return {"ok": True, "platform": "instagram_reel", "media_id": res["id"],
            "container": container, "status": status}


# ------------------------------------------------------------------ Facebook
def publish_facebook(payload: dict, cred: dict, dry: bool, video_state: str = "PUBLISHED") -> dict:
    """FB Reels - flow resmi v27.0: video_reels start -> rupload/video-upload -> finish."""
    need = ["page_id", "access_token"]
    missing = [k for k in need if not cred.get(k)]
    if missing:
        return {"ok": False, "error": f"kredensial Facebook kurang: {missing}"}
    video = Path(payload["video_path"])
    if not video.exists():
        return {"ok": False, "error": f"video tidak ada: {video}"}
    page = cred["page_id"]
    token = cred["access_token"]
    print(f"  [facebook] reels untuk page_id={page} (video_state={video_state})")
    if dry:
        return {"ok": True, "dry_run": True, "detail": "would publish reel: video_reels start -> upload -> finish"}
    # 1) mulai sesi upload
    start = http("POST", f"{GRAPH}/{page}/video_reels", json_body={
        "upload_phase": "start", "access_token": token})
    upload_url = start.get("upload_url")
    video_id = start.get("video_id")
    if not upload_url:
        return {"ok": False, "error": f"upload_phase start gagal: {str(start)[:250]}"}
    # 2) upload file (URL dari Meta sudah含 versi -> jangan ditambah)
    with open(video, "rb") as fh:
        raw = fh.read()
    up = http("POST", upload_url, headers={
        "Authorization": f"OAuth {token}", "offset": "0",
        "file_size": str(len(raw)), "Content-Type": "application/octet-stream",
    }, data=raw, timeout=900)
    if not (isinstance(up, dict) and up.get("success")):
        return {"ok": False, "error": f"upload gagal: {str(up)[:250]}"}
    # 3) selesaikan + publish
    fin = http("POST", f"{GRAPH}/{page}/video_reels", params={
        "video_id": video_id, "upload_phase": "finish", "video_state": video_state,
        "title": payload.get("title", ""), "description": payload.get("description", ""),
        "access_token": token})
    if not fin.get("success"):
        return {"ok": False, "error": f"upload_phase finish gagal: {str(fin)[:250]}"}
    return {"ok": True, "platform": "facebook_reel", "video_id": video_id,
            "video_state": video_state}


# -------------------------------------------------------------------- TikTok
TT_TOKEN_URL = f"{TIKTOK_API}/oauth/token/"


def _tt_http(method: str, url: str, **kw) -> dict:
    """http() yang tidak melempar exception saat 4xx (TikTok kirim detail di body)."""
    try:
        return http(method, url, **kw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return json.loads(body)
        except Exception:
            return {"_err": e.code, "_raw": body[:400]}


def tiktok_token(cred: dict, all_cred: dict) -> str:
    """Access token TikTok cuma 2 jam -> refresh otomatis pakai refresh_token (180 hari)."""
    now = int(time.time())
    exp = int(cred.get("expires_at") or 0)
    if cred.get("access_token") and (exp == 0 or now < exp - 180):
        return cred["access_token"]
    if not cred.get("refresh_token"):
        if cred.get("access_token"):
            return cred["access_token"]
        raise RuntimeError("token TikTok kosong — jalankan auth/tiktok_auth.py")
    body = urllib.parse.urlencode({
        "client_key": cred.get("client_key", ""),
        "client_secret": cred.get("client_secret", ""),
        "grant_type": "refresh_token",
        "refresh_token": cred["refresh_token"],
    }).encode()
    out = _tt_http("POST", TT_TOKEN_URL, headers={
        "Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
        data=body)
    if not out.get("access_token"):
        raise RuntimeError(f"refresh TikTok gagal: {str(out)[:200]}")
    cred["access_token"] = out["access_token"]
    if out.get("refresh_token"):
        cred["refresh_token"] = out["refresh_token"]
    cred["expires_at"] = now + int(out.get("expires_in", 0))
    if out.get("refresh_expires_in"):
        cred["refresh_expires_at"] = now + int(out["refresh_expires_in"])
    all_cred["tiktok"] = cred
    try:
        CRED_FILE.write_text(json.dumps(all_cred, indent=2, ensure_ascii=False), encoding="utf-8")
        CRED_FILE.chmod(0o600)
    except Exception:
        pass
    print("    [tiktok] access token di-refresh")
    return cred["access_token"]


def _tt_chunks(size: int) -> tuple[int, int]:
    """Aturan TikTok: <5MB -> 1 chunk; <=64MB -> 1 chunk; lebih -> 10MB/chunk."""
    if size <= 64 * 1024 * 1024:
        return size, 1
    cs = 10 * 1024 * 1024
    return cs, max(1, size // cs)


def publish_tiktok(payload: dict, cred: dict, dry: bool) -> dict:
    need = ["access_token"]
    missing = [k for k in need if not cred.get(k)]
    if missing:
        return {"ok": False, "error": f"kredensial TikTok kurang: {missing}"}
    video = Path(payload["video_path"])
    if not video.exists():
        return {"ok": False, "error": f"video tidak ada: {video}"}

    privacy = cred.get("privacy_level") or "SELF_ONLY"
    title = (payload.get("title") or "")[:2200]
    print(f"  [tiktok] post untuk @{cred.get('username', '?')} privacy={privacy}")
    if dry:
        return {"ok": True, "dry_run": True,
                "detail": "would publish via /post/publish/video/init/ + chunked PUT"}

    all_cred = load_credentials()
    token = tiktok_token(cred, all_cred)
    auth = {"Authorization": f"Bearer {token}"}

    # 1) wajib: query creator info sebelum posting (UX guideline TikTok)
    ci = _tt_http("POST", f"{TIKTOK_API}/post/publish/creator_info/query/",
                  headers={**auth, "Content-Type": "application/json; charset=UTF-8"},
                  json_body={})
    cinfo = ci.get("data") or {}
    options = cinfo.get("privacy_level_options") or []
    if options and privacy not in options:
        print(f"    [tiktok] privacy {privacy} tidak tersedia; pakai {options[0]}")
        privacy = options[0]
    maxdur = cinfo.get("max_video_post_duration_sec")
    if maxdur:
        print(f"    [tiktok] max durasi akun: {maxdur}s")

    # 2) init direct post (endpoint VIDEO, bukan content/init yang untuk foto)
    raw = video.read_bytes()
    chunk_size, total_chunks = _tt_chunks(len(raw))
    body = {
        "post_info": {
            "title": title,
            "privacy_level": privacy,
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": len(raw),
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunks,
        },
    }
    init = _tt_http("POST", f"{TIKTOK_API}/post/publish/video/init/",
                    headers={**auth, "Content-Type": "application/json; charset=UTF-8"},
                    json_body=body)
    data = init.get("data") or {}
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not upload_url:
        err = (init.get("error") or {})
        return {"ok": False, "error": f"video/init gagal: {err.get('code', '')} "
                                      f"{err.get('message', '')} {str(init)[:160]}"}
    print(f"    [tiktok] publish_id={publish_id} chunks={total_chunks} size={len(raw)}")

    # 3) upload chunk berurutan
    for i in range(total_chunks):
        start = i * chunk_size
        part = raw[start:start + chunk_size]
        end = start + len(part) - 1
        try:
            http("PUT", upload_url, headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(len(part)),
                "Content-Range": f"bytes {start}-{end}/{len(raw)}",
            }, data=part, timeout=900)
        except urllib.error.HTTPError as e:
            if e.code not in (201, 206):
                return {"ok": False, "error": f"upload chunk {i} HTTP {e.code}"}

    # 4) poll status
    status, fail = "PROCESSING", ""
    for _ in range(40):
        time.sleep(5)
        st = _tt_http("POST", f"{TIKTOK_API}/post/publish/status/fetch/",
                      headers={**auth, "Content-Type": "application/json; charset=UTF-8"},
                      json_body={"publish_id": publish_id})
        sd = st.get("data") or {}
        status = sd.get("status") or "UNKNOWN"
        fail = sd.get("fail_reason") or ""
        if status in ("PUBLISH_COMPLETE", "FAILED", "SEND_TO_USER_INBOX"):
            break
    ok = status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX")
    return {"ok": ok, "platform": "tiktok", "publish_id": publish_id,
            "status": status, "privacy": privacy, "error": fail or None}


PLATFORMS = {
    "youtube_shorts": publish_youtube,
    "instagram_reels": publish_instagram,
    "facebook_reels": publish_facebook,
    "tiktok": publish_tiktok,
}

# nama platform -> nama bagian di credentials.json
CRED_SECTION = {
    "youtube_shorts": "youtube",
    "instagram_reels": "instagram",
    "facebook_reels": "facebook",
    "tiktok": "tiktok",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="payload json episode")
    ap.add_argument("--publish", action="store_true", help="eksekusi upload (default: dry-run)")
    ap.add_argument("--only", help="comma separated platform keys")
    ap.add_argument("--privacy", default="public",
                    help="youtube privacyStatus: public|unlisted|private")
    ap.add_argument("--fb-state", default="PUBLISHED",
                    help="facebook video_state: PUBLISHED|DRAFT|SCHEDULED")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    cred = load_credentials()
    wanted = [p.strip() for p in (args.only or ",".join(PLATFORMS)).split(",") if p.strip()]
    print(f"payload : {payload['id']} - {payload['title']}")
    print(f"video   : {payload['video_path']}")
    print(f"mode    : {'PUBLISH' if args.publish else 'DRY-RUN'}\n")

    results = {}
    for name in wanted:
        fn = PLATFORMS.get(name)
        if fn is None:
            results[name] = {"ok": False, "error": "platform tidak dikenal"}
            continue
        try:
            section = cred.get(CRED_SECTION.get(name, name), {})
            if name == "youtube_shorts":
                results[name] = fn(payload, section, not args.publish, args.privacy)
            elif name == "facebook_reels":
                results[name] = fn(payload, section, not args.publish, args.fb_state)
            else:
                results[name] = fn(payload, section, not args.publish)
        except urllib.error.HTTPError as e:
            results[name] = {"ok": False, "error": f"HTTP {e.code}: {e.read().decode(errors='ignore')[:200]}"}
        except Exception as e:  # noqa: BLE001
            results[name] = {"ok": False, "error": repr(e)[:200]}
        print(f"  -> {results[name]}\n")

    entry = {
        "id": payload["id"], "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": "publish" if args.publish else "dry-run", "results": results,
    }
    log = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.append(entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(log[-200:], indent=2, ensure_ascii=False), encoding="utf-8")

    if args.publish:
        ok = all(r.get("ok") for r in results.values())
        print("SEMUA PLATFORM OK" if ok else "ADA PLATFORM GAGAL")
        return 0 if ok else 2
    print("dry-run selesai (tanpa upload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
