import json
import socket
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, urlunparse

MAX_SYNC_BODY_BYTES = 32 * 1024 * 1024


class BudgetSyncServer:
    def __init__(self, db, host="0.0.0.0", port=8765):
        self.db = db
        self.host = host
        self.port = port
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

            def do_GET(self):
                if self.path.rstrip("/") == "/status":
                    self._send_json(200, {
                        "ok": True,
                        "service": "BudgetApp Sync LAN",
                        "urls": outer.urls(),
                    })
                    return
                if self.path.rstrip("/") == "/transactions":
                    with outer.lock:
                        payload = outer.db.export_sync_payload()
                    self._send_json(200, payload)
                    return
                self._send_json(404, {"ok": False, "error": "Nieznany endpoint"})

            def do_POST(self):
                if self.path.rstrip("/") != "/sync":
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
                        payload = outer.db.export_sync_payload()
                    payload["ok"] = True
                    payload["imported"] = imported
                    self._send_json(200, payload)
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
    return {
        "imported_local": imported_local,
        "imported_remote": incoming.get("imported", {}),
        "peer": base_url,
    }
