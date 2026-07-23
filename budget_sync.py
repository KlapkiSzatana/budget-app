import json
import hashlib
import os
import socket
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote, urlparse, urlunparse

MAX_SYNC_BODY_BYTES = 32 * 1024 * 1024
MAX_SYNC_ATTACHMENT_BYTES = 512 * 1024 * 1024


class BudgetSyncServer:
    def __init__(self, db, host="0.0.0.0", port=8765, on_sync=None):
        self.db = db
        self.host = host
        self.port = port
        self.on_sync = on_sync
        self.httpd = None
        self.thread = None
        self.lock = threading.RLock()

    def start(self):
        if self.httpd:
            return

        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def _send_json(self, code, payload):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                if len(body) > MAX_SYNC_BODY_BYTES:
                    code = 500
                    payload = {"ok": False, "error": "Odpowiedź synchronizacji jest za duża"}
                    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_file(self, path):
                if not path or not os.path.isfile(path):
                    self._send_json(404, {"ok": False, "error": "Nie znaleziono załącznika"})
                    return
                size = os.path.getsize(path)
                if size > MAX_SYNC_ATTACHMENT_BYTES:
                    self._send_json(413, {"ok": False, "error": "Załącznik jest za duży"})
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(size))
                self.end_headers()
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        self.wfile.write(chunk)

            def do_GET(self):
                path = self.path.split("?", 1)[0].rstrip("/") or "/"
                if path.startswith("/attachment/"):
                    sync_id = unquote(path[len("/attachment/"):])
                    with outer.lock:
                        file_path = outer.db.sync_attachment_file(sync_id)
                    self._send_file(file_path)
                    return
                if path == "/status":
                    self._send_json(200, {
                        "ok": True,
                        "service": "BudgetApp Sync LAN",
                        "urls": outer.urls(),
                    })
                    return
                if path == "/transactions":
                    with outer.lock:
                        payload = outer.db.export_sync_payload()
                    self._send_json(200, payload)
                    return
                self._send_json(404, {"ok": False, "error": "Nieznany endpoint"})

            def do_POST(self):
                if self.path.split("?", 1)[0].rstrip("/") != "/sync":
                    self._send_json(404, {"ok": False, "error": "Nieznany endpoint"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > MAX_SYNC_BODY_BYTES:
                        self._send_json(413, {"ok": False, "error": "Dane synchronizacji są za duże"})
                        return
                    raw = self.rfile.read(length).decode("utf-8")
                    incoming = json.loads(raw) if raw else {}
                    with outer.lock:
                        imported = outer.db.import_sync_payload(incoming)
                    peer_base = peer_base_url_from_payload(incoming)
                    if not peer_base and self.client_address:
                        peer_base = f"http://{self.client_address[0]}:8765"
                    attachments = download_missing_sync_attachments(outer.db, peer_base, incoming, lock=outer.lock)
                    imported["attachments_downloaded"] = attachments.get("downloaded", 0)
                    imported["attachment_errors"] = attachments.get("errors", 0)
                    with outer.lock:
                        payload = outer.db.export_sync_payload()
                    payload["ok"] = True
                    payload["imported"] = imported
                    self._send_json(200, payload)
                    outer._notify_sync_received(imported, attachments, self.client_address)
                except Exception as exc:
                    self._send_json(500, {"ok": False, "error": str(exc)})

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.httpd:
            return
        self.httpd.shutdown()
        self.httpd.server_close()
        self.httpd = None
        self.thread = None

    def is_running(self):
        return self.httpd is not None

    def urls(self):
        return [f"http://{ip}:{self.port}" for ip in local_ipv4_addresses()]

    def _notify_sync_received(self, imported, attachments, client_address=None):
        if not self.on_sync:
            return
        try:
            self.on_sync({
                "imported": imported or {},
                "attachments": attachments or {},
                "client": client_address[0] if client_address else "",
            })
        except Exception:
            pass


def local_ipv4_addresses():
    addresses = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in addresses:
                addresses.append(ip)
    except Exception:
        pass

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        if ip and not ip.startswith("127.") and ip not in addresses:
            addresses.append(ip)
    except Exception:
        pass

    if not addresses:
        addresses.append("127.0.0.1")
    return addresses


def normalize_sync_url(raw_url):
    url = str(raw_url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.endswith("/sync"):
        path = path[:-5]
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")).rstrip("/")


def peer_base_url_from_payload(payload):
    if not isinstance(payload, dict):
        return ""
    urls = payload.get("device_urls") or []
    if isinstance(urls, str):
        urls = [urls]
    for url in urls:
        normalized = normalize_sync_url(url)
        if normalized:
            return normalized
    return ""


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _with_optional_lock(lock, func):
    if lock is None:
        return func()
    with lock:
        return func()


def download_missing_sync_attachments(db, peer_url, payload, lock=None, timeout=120):
    """Dociąga załączniki opisane w payloadzie bez wkładania ich do JSON-a."""
    base_url = normalize_sync_url(peer_url)
    result = {"downloaded": 0, "errors": 0}
    if not base_url or not isinstance(payload, dict):
        return result

    rows = payload.get("transactions") or []
    if not isinstance(rows, list):
        return result

    for tx in rows:
        if not isinstance(tx, dict) or not tx.get("attachment_present"):
            continue
        sync_id = str(tx.get("sync_id") or "").strip()
        if not sync_id:
            continue
        try:
            expected_size = int(tx.get("attachment_size", -1))
        except Exception:
            expected_size = -1
        expected_sha = str(tx.get("attachment_sha256") or "").strip().lower()

        needs_download = _with_optional_lock(
            lock,
            lambda: db.needs_sync_attachment_download(sync_id, expected_size, expected_sha)
        )
        if not needs_download:
            continue

        tmp_path = None
        try:
            request = urllib.request.Request(
                base_url + "/attachment/" + quote(sync_id, safe=""),
                method="GET",
                headers={"Accept": "application/octet-stream"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_SYNC_ATTACHMENT_BYTES:
                    raise RuntimeError("Załącznik jest za duży")
                fd, tmp_path = tempfile.mkstemp(prefix="budget-sync-attachment-", suffix=".tmp")
                os.close(fd)
                digest = hashlib.sha256()
                total = 0
                with open(tmp_path, "wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_SYNC_ATTACHMENT_BYTES:
                            raise RuntimeError("Załącznik jest za duży")
                        digest.update(chunk)
                        f.write(chunk)
            if expected_size >= 0 and os.path.getsize(tmp_path) != expected_size:
                raise RuntimeError("Niepełny załącznik")
            if expected_sha and digest.hexdigest().lower() != expected_sha:
                raise RuntimeError("Nieprawidłowy załącznik")

            saved = _with_optional_lock(
                lock,
                lambda: db.save_sync_attachment(sync_id, tx.get("attachment_name") or "zalacznik.dat", tmp_path)
            )
            if saved:
                result["downloaded"] += 1
            else:
                result["errors"] += 1
        except Exception:
            result["errors"] += 1
        finally:
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    return result


def post_sync_payload(peer_url, payload, timeout=20):
    """Wysyła gotowy payload do drugiego urządzenia i zwraca odpowiedź JSON."""
    base_url = normalize_sync_url(peer_url)
    if not base_url:
        raise ValueError("Brak adresu drugiego urządzenia")

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_SYNC_BODY_BYTES:
        raise ValueError("Dane synchronizacji są za duże")
    request = urllib.request.Request(
        base_url + "/sync",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_SYNC_BODY_BYTES:
                raise RuntimeError("Odpowiedź synchronizacji jest za duża")
            data = response.read(MAX_SYNC_BODY_BYTES + 1)
            if len(data) > MAX_SYNC_BODY_BYTES:
                raise RuntimeError("Odpowiedź synchronizacji jest za duża")
            raw = data.decode("utf-8")
    except urllib.error.HTTPError as exc:
        data = exc.read(MAX_SYNC_BODY_BYTES + 1)
        if len(data) > MAX_SYNC_BODY_BYTES:
            raise RuntimeError("Odpowiedź błędu synchronizacji jest za duża") from exc
        raw = data.decode("utf-8", errors="replace")
        message = raw
        try:
            decoded = json.loads(raw) if raw else {}
            if isinstance(decoded, dict):
                message = decoded.get("error") or decoded.get("message") or raw
        except Exception:
            pass
        raise RuntimeError(message or f"HTTP {exc.code}") from exc

    incoming = json.loads(raw) if raw else {}
    if not isinstance(incoming, dict):
        raise RuntimeError("Nieprawidłowa odpowiedź urządzenia")
    if isinstance(incoming, dict) and incoming.get("ok") is False:
        raise RuntimeError(str(incoming.get("error") or "Urządzenie zwróciło błąd synchronizacji"))
    return incoming


def sync_with_peer(db, peer_url, timeout=20):
    """Wysyła lokalny payload do drugiego urządzenia i scala odpowiedź."""
    base_url = normalize_sync_url(peer_url)
    payload = db.export_sync_payload()
    incoming = post_sync_payload(base_url, payload, timeout=timeout)
    imported_local = db.import_sync_payload(incoming)
    attachments = download_missing_sync_attachments(db, base_url, incoming, timeout=max(timeout, 120))
    return {
        "imported_local": imported_local,
        "attachments": attachments,
        "imported_remote": incoming.get("imported", {}),
        "peer": base_url,
    }
