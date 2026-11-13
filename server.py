"""Local-only CareLedger app with a SQLite database stored beside this file."""

from __future__ import annotations

import json
import sqlite3
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "data"
DB_PATH = DB_DIR / "patient-registry.sqlite3"
HOST = "127.0.0.1"
PORT = 8765
MAX_BODY_BYTES = 25 * 1024 * 1024


def connect_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


class CareLedgerHandler(BaseHTTPRequestHandler):
    server_version = "CareLedgerLocal/1.0"

    def log_message(self, _format: str, *_args: object) -> None:
        # Avoid writing patient-related request details to the console log.
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _is_local_request(self) -> bool:
        # The service only binds to loopback. Also reject cross-origin requests
        # and unexpected Host headers to reduce exposure to other websites.
        allowed_hosts = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
        if self.headers.get("Host", "").lower() not in allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {
            f"http://127.0.0.1:{PORT}",
            f"http://localhost:{PORT}",
        }

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._is_local_request():
            self._json(403, {"error": "Local requests only"})
            return

        path = urlparse(self.path).path
        if path == "/api/patients":
            try:
                with connect_db() as db:
                    rows = db.execute(
                        "SELECT data_json FROM patients ORDER BY lower(name), id"
                    ).fetchall()
                patients = [json.loads(row["data_json"]) for row in rows]
                self._json(200, patients)
            except (sqlite3.Error, json.JSONDecodeError) as exc:
                self._json(500, {"error": f"Could not read the local database: {exc}"})
            return

        if path in {"/", "/index.html"}:
            try:
                body = (ROOT / "index.html").read_bytes()
            except OSError:
                self._send(500, b"App file is missing.", "text/plain; charset=utf-8")
                return
            self._send(200, body, "text/html; charset=utf-8")
            return

        self._send(404, b"Not found.", "text/plain; charset=utf-8")

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._is_local_request():
            self._json(403, {"error": "Local requests only"})
            return
        if urlparse(self.path).path != "/api/patients":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "Invalid request size"})
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self._json(413, {"error": "Registry is too large for one save"})
            return
        try:
            incoming = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "Invalid JSON data"})
            return
        if not isinstance(incoming, list):
            self._json(400, {"error": "Expected a list of patient records"})
            return

        records: list[tuple[str, str, str, str]] = []
        for record in incoming:
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("id"), str)
                or not isinstance(record.get("name"), str)
                or not record["name"].strip()
            ):
                self._json(400, {"error": "A patient record is missing its ID or name"})
                return
            records.append(
                (
                    record["id"],
                    record["name"].strip(),
                    json.dumps(record, ensure_ascii=False),
                    str(record.get("updated", "")),
                )
            )

        try:
            with connect_db() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("DELETE FROM patients")
                db.executemany(
                    "INSERT INTO patients(id, name, data_json, updated) VALUES (?, ?, ?, ?)",
                    records,
                )
                db.commit()
            self._json(200, {"saved": len(records)})
        except sqlite3.Error as exc:
            self._json(500, {"error": f"Could not save the local database: {exc}"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), CareLedgerHandler)
    url = f"http://{HOST}:{PORT}/"
    print("CareLedger is running on this PC only.")
    print(f"App: {url}")
    print(f"Database file: {DB_PATH}")
    print("Leave this window open while using the app. Press Ctrl+C to stop it.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCareLedger stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
