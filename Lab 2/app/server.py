from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, HTTPServer
from typing import Optional
from functools import partial
import json
from collections import deque
from urllib.parse import urlsplit

from .counter import NaiveCounter, LockedCounter
from .rate_limiter import RateLimiter


def getenv_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


class Config:
    def __init__(self) -> None:
        self.port = getenv_int("SERVER_PORT", 8000)
        self.doc_root = os.getenv("DOC_ROOT", os.getcwd())
        self.delay = getenv_float("HANDLER_DELAY", 1.0)
        self.counter_mode = os.getenv("COUNTER_MODE", "locked")  # naive or locked
        self.rps = getenv_float("RATE_LIMIT_RPS", 5.0)
        self.burst = getenv_int("RATE_LIMIT_BURST", 10)
        self.server_type = os.getenv("SERVER_TYPE", "threaded")  # single or threaded
        self.trust_xff = os.getenv("TRUST_XFF", "false").lower() in {"1", "true", "yes"}


class RequestHandler(SimpleHTTPRequestHandler):
    counter = None  # type: ignore
    limiter = None  # type: ignore
    delay = 1.0
    inflight = 0
    inflight_lock = threading.Lock()
    # recent logs buffer
    logs = deque(maxlen=1000)
    logs_lock = threading.Lock()
    log_seq = 0

    # Reduce noisy logging
    def log_message(self, format: str, *args) -> None:  # noqa: A003 - name from base class
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def do_GET(self) -> None:  # noqa: N802 - base class method name
        # Determine client IP (optionally trust X-Forwarded-For for local testing)
        hdr_xff = self.headers.get("X-Forwarded-For")
        if getattr(self, "trust_xff", False) and hdr_xff:
            ip = hdr_xff.split(",")[0].strip()
        else:
            ip = self.client_address[0]

        # Special endpoint to expose current counters (no delay, not counted)
        if self.path == "/__counts":
            snap = self.counter.snapshot() if self.counter else {}
            # normalize keys by stripping query strings
            data: dict[str, int] = {}
            for k, v in snap.items():
                p = urlsplit(k).path
                data[p] = data.get(p, 0) + v
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Simple JSON API for UI
        if self.path.startswith("/api/"):
            self._handle_api(ip)
            return

        # Rate limit only non-API requests
        if self.limiter and not self.limiter.allow(ip):
            self.send_error(HTTPStatus.TOO_MANY_REQUESTS, "Rate limit exceeded")
            # log rejection
            self._log(ip=ip, method="GET", path=self.path, status=int(HTTPStatus.TOO_MANY_REQUESTS), dur_ms=0.0, inflight=self._inflight_peek())
            return

        # Track inflight for non-API work to visualize concurrency
        start = time.monotonic()
        self._inflight_inc()
        self._last_status = None  # type: ignore[attr-defined]
        try:
            # simulate work
            time.sleep(self.delay)

            # increment per-file counter (path as key)
            # normalize to path-only (ignore query) so cache-busting params don't fragment counts
            key = urlsplit(self.path).path
            if self.counter:
                self.counter.inc(key)

            # For directory listing, inject counts at top if requesting a directory
            if self.path.endswith('/') or self.path == '/':
                counts = self.counter.snapshot() if self.counter else {}
                self._serve_custom_index(counts, document_root=self.directory or os.getcwd())
                return

            super().do_GET()
        except Exception as e:
            # Log as error-like entry with status 499 (client closed) if appropriate
            dur_ms = (time.monotonic() - start) * 1000.0
            infl = self._inflight_peek()
            status = getattr(self, "_last_status", None)
            status = int(status) if status is not None else 499
            self._log(ip=ip, method="GET", path=self.path, status=status, dur_ms=dur_ms, inflight=infl)
            raise
        finally:
            dur_ms = (time.monotonic() - start) * 1000.0
            infl = self._inflight_peek()
            status = getattr(self, "_last_status", None)
            if status is None:
                status = 200
            self._log(ip=ip, method="GET", path=self.path, status=int(status), dur_ms=dur_ms, inflight=infl)
            self._inflight_dec()

    # capture status codes for accurate logging
    def send_response(self, code: int, message: str | None = None) -> None:  # type: ignore[override]
        try:
            self._last_status = code  # type: ignore[attr-defined]
        except Exception:
            pass
        return super().send_response(code, message)

    # add no-store cache headers for non-API resources to ensure UI demos hit the server
    def end_headers(self) -> None:  # type: ignore[override]
        try:
            if not self.path.startswith("/api/"):
                # prevent browser cache from short-circuiting requests
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
        except Exception:
            pass
        return super().end_headers()

    def _handle_api(self, ip: str) -> None:
        # /api/ping -> { ok: true }
        if self.path.startswith("/api/ping"):
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/info -> config snapshot
        if self.path.startswith("/api/info"):
            data = {
                "delay": self.delay,
                "counter_mode": type(self.counter).__name__ if self.counter else None,
                "rps": getattr(self.limiter, "_rps", None),
                "burst": getattr(self.limiter, "_burst", None),
                "server": "threaded" if isinstance(self.server, ThreadingHTTPServer) else "single",
            }
            body = json.dumps(data).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/reset -> clear counters
        if self.path.startswith("/api/reset"):
            if self.counter:
                try:
                    self.counter.reset()
                except Exception:
                    pass
            body = json.dumps({"reset": True}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/counter -> current counts (normalized by path)
        if self.path.startswith("/api/counter"):
            snap = self.counter.snapshot() if self.counter else {}
            data: dict[str, int] = {}
            for k, v in snap.items():
                p = urlsplit(k).path
                data[p] = data.get(p, 0) + v
            body = json.dumps(data).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/inflight -> number of in-progress non-API requests
        if self.path.startswith("/api/inflight"):
            with type(self).inflight_lock:
                n = type(self).inflight
            body = json.dumps({"inflight": n}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/logs?since=<id>&last=<n> -> recent logs
        if self.path.startswith("/api/logs"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            try:
                since = int(q.get("since", ["0"])[0])
            except ValueError:
                since = 0
            try:
                last = int(q.get("last", ["100"])[0])
            except ValueError:
                last = 100
            last = max(1, min(500, last))
            with type(self).logs_lock:
                items = list(type(self).logs)
            if since > 0:
                items = [e for e in items if e.get("id", 0) > since]
            else:
                items = items[-last:]
            body = json.dumps(items).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # /api/fire?path=/index.html&n=20 -> server-side generator of N requests (useful to visualize concurrency)
        if self.path.startswith("/api/fire"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            path = q.get("path", ["/"])[0]
            try:
                n = int(q.get("n", ["10"])[0])
            except ValueError:
                n = 10
            # Fire concurrent requests to our own server using threads
            import concurrent.futures, urllib.request
            url = f"http://127.0.0.1:{self.server.server_port}{path}"
            def fetch(u: str) -> int:
                try:
                    with urllib.request.urlopen(u) as r:
                        return r.status
                except Exception:
                    return -1
            oks = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(64, n)) as ex:
                for s in concurrent.futures.as_completed([ex.submit(fetch, url) for _ in range(n)]):
                    if s.result() == 200:
                        oks += 1
            body = json.dumps({"requested": n, "ok": oks}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Fallback 404
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API path")

    def _render_counts(self, counts: dict[str, int]) -> str:
        rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in sorted(counts.items()))
        return f"<table border='1'><tr><th>Path</th><th>Count</th></tr>{rows}</table>"

    def _serve_custom_index(self, counts: dict[str, int], document_root: str) -> None:
        # list files in document_root
        try:
            items = sorted(os.listdir(document_root))
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "Directory not found")
            return
        links = []
        # ensure base path ends with '/'
        base = self.path if self.path.endswith('/') else self.path + '/'
        for name in items:
            path = name + ('/' if os.path.isdir(os.path.join(document_root, name)) else '')
            href = base + path
            c = counts.get(href, 0)
            links.append(f"<li><a href='{href}'>{path}</a> — requests: {c}</li>")
        body = f"""
        <html><head><title>Index</title></head>
        <body>
          <h1>Directory listing for {self.path}</h1>
          <p>Artificial handler delay: {self.delay:.3f}s</p>
          <ul>
            {''.join(links)}
          </ul>
        </body></html>
        """
        body_bytes = body.encode('utf-8', 'replace')
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _inflight_inc(self) -> None:
        with type(self).inflight_lock:
            type(self).inflight += 1

    def _inflight_dec(self) -> None:
        with type(self).inflight_lock:
            if type(self).inflight > 0:
                type(self).inflight -= 1

    def _inflight_peek(self) -> int:
        with type(self).inflight_lock:
            return type(self).inflight

    def _log(self, *, ip: str, method: str, path: str, status: int, dur_ms: float, inflight: int) -> None:
        with type(self).logs_lock:
            type(self).log_seq += 1
            entry = {
                "id": type(self).log_seq,
                "ts": time.time(),
                "ip": ip,
                "method": method,
                "path": path,
                "status": status,
                "dur_ms": round(dur_ms, 2),
                "inflight": inflight,
                "thread": threading.current_thread().name,
            }
            type(self).logs.append(entry)


def make_server(cfg: Config) -> tuple[HTTPServer, type[RequestHandler]]:
    # Choose counter
    counter = NaiveCounter() if cfg.counter_mode == "naive" else LockedCounter()
    # Limiter
    limiter = RateLimiter(cfg.rps, cfg.burst)

    # Bind handler class with shared state
    class Handler(RequestHandler):
        pass
    # Assign attributes outside class body to avoid scope issues
    Handler.counter = counter  # type: ignore[attr-defined]
    Handler.limiter = limiter  # type: ignore[attr-defined]
    Handler.delay = cfg.delay  # type: ignore[attr-defined]
    Handler.directory = cfg.doc_root  # type: ignore[attr-defined]
    Handler.trust_xff = cfg.trust_xff  # type: ignore[attr-defined]

    # Ensure handler serves from configured directory by passing it explicitly
    handler_factory = partial(Handler, directory=cfg.doc_root)

    if cfg.server_type == "threaded":
        httpd: HTTPServer = ThreadingHTTPServer(("0.0.0.0", cfg.port), handler_factory)
    else:
        httpd = HTTPServer(("0.0.0.0", cfg.port), handler_factory)

    # Allow quick restarts
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return httpd, Handler


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Simple concurrent HTTP server with rate limiting and counters")
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", 8000)))
    parser.add_argument("--doc-root", type=str, default=os.getenv("DOC_ROOT", os.getcwd()))
    parser.add_argument("--delay", type=float, default=float(os.getenv("HANDLER_DELAY", 1.0)))
    parser.add_argument("--counter", choices=["naive", "locked"], default=os.getenv("COUNTER_MODE", "locked"))
    parser.add_argument("--rps", type=float, default=float(os.getenv("RATE_LIMIT_RPS", 5.0)))
    parser.add_argument("--burst", type=int, default=int(os.getenv("RATE_LIMIT_BURST", 10)))
    parser.add_argument("--server", choices=["single", "threaded"], default=os.getenv("SERVER_TYPE", "threaded"))
    args = parser.parse_args(argv)

    cfg = Config()
    cfg.port = args.port
    cfg.doc_root = args.doc_root
    cfg.delay = args.delay
    cfg.counter_mode = args.counter
    cfg.rps = args.rps
    cfg.burst = args.burst
    cfg.server_type = args.server

    httpd, _ = make_server(cfg)

    server_kind = "Threaded" if cfg.server_type == "threaded" else "Single-threaded"
    print(f"Starting {server_kind} HTTP server on port {cfg.port}, doc_root={cfg.doc_root}, counter={cfg.counter_mode}, rps={cfg.rps}/s, burst={cfg.burst}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
