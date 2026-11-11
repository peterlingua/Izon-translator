"""Small local browser interface for the Kolokuma Izon translator."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import html
import json
import webbrowser
import threading
from pathlib import Path

from translator import translate
import translator
import lexicon
from lexicon import load_lexicon, lookup_english_word, lookup_izon_word

import os
# Local use: 127.0.0.1:8000. On a hosting service the platform sets PORT
# and we must listen on all interfaces (HOST=0.0.0.0).
DEPLOYED = "PORT" in os.environ
HOST = os.environ.get("HOST", "0.0.0.0" if DEPLOYED else "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Kolokuma Izon ↔ English Translator</title>
<link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#203b70">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Izon Translator">
<link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#172033;background:#f3f6fb}
*{box-sizing:border-box}body{margin:0;padding:28px 14px}.wrap{max-width:850px;margin:auto}
header{text-align:center;margin:12px 0 26px}h1{font-size:clamp(1.5rem,4vw,2.3rem);margin-bottom:8px}
.sub{color:#596579}.card{background:white;border:1px solid #dfe5ef;border-radius:18px;padding:22px;box-shadow:0 10px 28px #1720330c}
.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
select,textarea,button{font:inherit;font-size:16px;border-radius:10px;border:1px solid #cbd5e1;padding:12px;min-height:44px}
select{background:white}textarea{width:100%;min-height:145px;resize:vertical;line-height:1.5}
button{cursor:pointer;background:#203b70;color:white;border-color:#203b70;font-weight:600}
button.secondary{background:white;color:#203b70}
.labels{display:flex;justify-content:space-between;color:#596579;font-size:.92rem;margin:12px 0 8px}
.result{white-space:pre-wrap;min-height:110px;background:#f7f9fc;border:1px solid #e1e7f0;border-radius:12px;padding:16px;line-height:1.6;overflow-wrap:anywhere}
.note{font-size:.9rem;color:#596579;line-height:1.5;margin-top:18px}.footer{text-align:center;font-size:.85rem;color:#697386;margin:20px}
@media(max-width:560px){body{padding:14px 9px}.card{padding:15px}.controls>*{flex:1}}
</style></head><body><main class="wrap">
<header><h1>Kolokuma Izon ↔ English</h1><div class="sub">Rule-based sentence translation</div></header>
<section class="card">
<form method="post" action="/translate">
<div class="controls"><label for="direction"><strong>Translation direction</strong></label>
<select id="direction" name="direction">
<option value="english_to_izon" {{EN_SELECTED}}>English → Izon</option>
<option value="izon_to_english" {{IZ_SELECTED}}>Izon → English</option>
</select>
<button type="submit">Translate sentence</button>
<button class="secondary" type="button" onclick="document.getElementById('source').value='';document.getElementById('result').textContent='';">Clear</button></div>
<div class="labels"><label for="source">Enter your sentence</label><span>Supports Izon diacritics</span></div>
<textarea id="source" name="source" placeholder="Type a sentence here..." autofocus>{{SOURCE}}</textarea>
<div class="labels"><strong>Translation</strong><button class="secondary" type="button" onclick="navigator.clipboard?.writeText(document.getElementById('result').textContent)">Copy result</button></div>
<div id="result" class="result">{{RESULT}}</div>
</form>
<div class="note"><strong>Research note:</strong> This is a rule-based prototype, not a complete production translator. It composes some unseen sentences from reusable grammar patterns, but only for patterns implemented in the code. Unsupported question structures are marked rather than guessed. Generated Izon forms need review by a fluent Kolokuma speaker; words the system cannot recognize may be marked as unknown.</div>
</section><div class="footer">Runs locally on your computer. No account or internet connection is required.</div>
</main><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/sw.js")}</script></body></html>"""

def render(source="", result="", direction="english_to_izon"):
    page = PAGE.replace("{{SOURCE}}", html.escape(source)).replace("{{RESULT}}", html.escape(result))
    page = page.replace("{{EN_SELECTED}}", "selected" if direction == "english_to_izon" else "")
    page = page.replace("{{IZ_SELECTED}}", "selected" if direction == "izon_to_english" else "")
    return page.encode("utf-8")

import struct
import zlib


def make_icon_png(size: int) -> bytes:
    """Draw a solid app icon with two white bars (a translation arrow pair)."""
    blue, white = (32, 59, 112), (255, 255, 255)
    bar = max(2, int(size * 0.06))
    rows = []
    for y in range(size):
        row = bytearray([0])  # PNG filter byte
        for x in range(size):
            in_bar_x = 0.2 * size <= x <= 0.8 * size
            near_bar = any(abs(y - int(size * f)) < bar / 2 + 0.5 for f in (0.4, 0.6))
            color = white if (in_bar_x and near_bar) else blue
            row.extend(color)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


SERVICE_WORKER = """
const CACHE = 'izon-translator-v1';
const SHELL = ['/'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;  // translations are always sent to the server
  e.respondWith(
    fetch(e.request).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put('/', copy)).catch(() => {});
      return r;
    }).catch(() => caches.match('/'))
  );
});
"""


class Handler(BaseHTTPRequestHandler):
    def _send_bytes(self, payload, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, value, status=200):
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._send_bytes(payload, "application/json; charset=utf-8", status)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            try:
                loaded = load_lexicon()
                self._send_json({
                    "status": "ok",
                    "dictionary_source": loaded.get("source"),
                    "dictionary_rows": loaded.get("row_count", 0),
                    "usable_entries": len(loaded.get("entries", [])),
                    "dictionary_file": str(lexicon.DICTIONARY_FILE.resolve()),
                    "translator_file": str(Path(translator.__file__).resolve()),
                })
            except Exception as exc:
                self._send_json({"status": "error", "error": str(exc)}, 500)
            return
        if parsed.path == "/api/lookup":
            params = parse_qs(parsed.query, keep_blank_values=True)
            word = params.get("word", [""])[0].strip()
            direction = params.get("direction", ["izon_to_english"])[0]
            if direction not in ("english_to_izon", "izon_to_english"):
                direction = "izon_to_english"
            if not word:
                self._send_json({"word": "", "direction": direction, "matches": []}, 400)
                return
            try:
                loaded = load_lexicon()
                matches = (lookup_english_word(word, loaded) if direction == "english_to_izon"
                           else lookup_izon_word(word, loaded))
                self._send_json({"word": word, "direction": direction, "matches": [
                    {"izon": row.get("izon", ""), "english": row.get("english", ""),
                     "full_english": row.get("full_english", ""),
                     "part_of_speech": row.get("part_of_speech", "")}
                    for row in matches
                ]})
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
            return
        if parsed.path == "/manifest.webmanifest":
            manifest = {
                "name": "Kolokuma Izon ↔ English Translator",
                "short_name": "Izon Translator",
                "start_url": "/", "scope": "/", "display": "standalone",
                "background_color": "#f3f6fb", "theme_color": "#203b70",
                "icons": [
                    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            }
            self._send_bytes(json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
                             "application/manifest+json; charset=utf-8")
            return
        if parsed.path in ("/icon-192.png", "/icon-512.png", "/apple-touch-icon.png"):
            size = {"/icon-192.png": 192, "/icon-512.png": 512, "/apple-touch-icon.png": 180}[parsed.path]
            self._send_bytes(make_icon_png(size), "image/png")
            return
        if parsed.path == "/sw.js":
            # Minimal service worker: makes the app installable and keeps the
            # shell available when offline. Translation itself needs the server.
            self._send_bytes(SERVICE_WORKER.encode("utf-8"), "application/javascript; charset=utf-8")
            return
        # Prevent a browser from reusing an older rendered page after the server restarts.
        self._send_bytes(render(), "text/html; charset=utf-8")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        content_type = self.headers.get("Content-Type", "")
        parsed = urlparse(self.path)
        try:
            if "application/json" in content_type:
                fields = json.loads(body or "{}")
            else:
                fields = parse_qs(body, keep_blank_values=True)
                fields = {key: values[0] if values else "" for key, values in fields.items()}
            source = str(fields.get("source", "") or "")
            direction = str(fields.get("direction", "english_to_izon") or "english_to_izon")
            if direction not in ("english_to_izon", "izon_to_english"):
                direction = "english_to_izon"
            result = translate(source, direction)
        except Exception as exc:
            if parsed.path == "/api/translate":
                self._send_json({"error": str(exc)}, 400)
                return
            source = ""
            direction = "english_to_izon"
            result = f"Translation error: {exc}"
        if parsed.path == "/api/translate":
            self._send_json({"source": source, "direction": direction, "translation": result})
            return
        self._send_bytes(render(source, result, direction), "text/html; charset=utf-8")

    def log_message(self, fmt, *args):
        print("[web]", fmt % args)

if __name__ == "__main__":
    # If an older copy is still running on port 8000, do not silently fail
    # and leave the user looking at that old copy. Choose the next free port.
    selected_port = PORT
    if DEPLOYED:
        # The hosting platform owns the port; do not search for another one.
        server = ThreadingHTTPServer((HOST, selected_port), Handler)
    else:
        while True:
            try:
                server = ThreadingHTTPServer((HOST, selected_port), Handler)
                break
            except OSError as exc:
                if getattr(exc, "errno", None) not in (48, 98, 10048):
                    raise
                selected_port += 1
                if selected_port > PORT + 20:
                    raise RuntimeError("Could not find a free local port for the browser interface.") from exc
    url = f"http://{HOST}:{selected_port}/"
    print("=" * 58)
    print("KOLOKUMA IZON TRANSLATOR - BROWSER APP")
    print(f"Open {url} in your browser. Keep this window open while using it.")
    print("Press Ctrl+C in this window to stop the app.")
    print(f"Web interface file: {Path(__file__).resolve()}")
    print(f"Translation engine:  {Path(translator.__file__).resolve()}")
    print(f"Dictionary CSV:      {lexicon.DICTIONARY_FILE.resolve()}")
    print("Test check: 'girl' ->", translate("girl", "english_to_izon"))
    print("Test check: 'the girl' ->", translate("the girl", "english_to_izon"))
    print("Test check: 'who is the girl' ->", translate("who is the girl", "english_to_izon"))
    print("=" * 58)
    if not DEPLOYED:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTranslator stopped.")
    finally:
        server.server_close()
