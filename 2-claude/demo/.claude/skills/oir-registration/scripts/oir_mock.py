#!/usr/bin/env python3
"""Local stand-in for the Ondura Interlibrary Registry (OIR) service.

In a real project this would be a remote service owned by another team. Here
it runs on localhost so the lab is self-contained. Standard library only.

    python3 oir_mock.py [--port 8787]

State is in memory and resets when the server stops.
"""

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

CHECK_ALPHABET = "BCDFGHJKLMNPQRSTVWXZ"
OATH = "By quill and lamplight, I petition Ondura"
PROBATION_TICKS = 3
ATTEST_DEADLINE_TICKS = 2
SEALS_PER_AUTHOR = 3
EARLIEST_YEAR = 1450

SEAL_RE = re.compile(r"^OIR-[A-Z]{2}-\d{4}-[A-Z]$")


def shelf_for(author: str) -> str:
    surname = author.strip().split()[-1].upper()
    consonants = [c for c in surname if c.isalpha() and c not in "AEIOU"]
    return "".join(consonants[:2]).ljust(2, "X")


def check_char(shelf: str, year: int) -> str:
    total = sum(int(d) for d in f"{year:04d}") + sum(ord(c) - 64 for c in shelf)
    return CHECK_ALPHABET[(total * 7) % 20]


def seal_for(author: str, year: int) -> str:
    shelf = shelf_for(author)
    return f"OIR-{shelf}-{year:04d}-{check_char(shelf, year)}"


SEALS: dict[str, dict] = {}
APPLICATIONS: dict[str, dict] = {}
_next_app = 1


def seed() -> None:
    for title, author, year in [
        ("Dune", "Frank Herbert", 1965),
        ("Emma", "Jane Austen", 1815),
    ]:
        SEALS[seal_for(author, year)] = {"title": title, "author": author, "year": year}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the lab's terminal quiet
        pass

    def _send(self, status: int, body: dict) -> None:
        payload = json.dumps(body, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        path = self.path.rstrip("/")
        if path in ("/v1/health", ""):
            return self._send(200, {"service": "ondura-interlibrary-registry", "version": "1.4"})
        if path == "/v1/applications":
            return self._send(200, {"applications": list(APPLICATIONS.values())})
        if path.startswith("/v1/applications/"):
            app = APPLICATIONS.get(path.rsplit("/", 1)[-1])
            if app is None:
                return self._send(404, {"code": "UNKNOWN_APPLICATION"})
            return self._send(200, app)
        if path.startswith("/v1/seals/"):
            code = path.rsplit("/", 1)[-1]
            if code not in SEALS:
                return self._send(404, {"code": "UNKNOWN_SEAL"})
            return self._send(200, {"seal": code, **SEALS[code]})
        return self._send(404, {"code": "NO_SUCH_ROUTE"})

    def do_POST(self):
        global _next_app
        path = self.path.rstrip("/")
        body = self._body()

        if path == "/v1/applications":
            title = body.get("title", "")
            author = body.get("author", "")
            year = body.get("year", 0)
            sponsor = body.get("sponsor_seal", "")
            if not isinstance(year, int) or year < EARLIEST_YEAR:
                return self._send(451, {"code": "EMBARGOED_YEAR", "earliest": EARLIEST_YEAR})
            if len(title) > 64:
                return self._send(422, {"code": "TITLE_TOO_LONG", "limit": 64})
            sponsor_record = SEALS.get(sponsor)
            if sponsor_record is None or sponsor_record["author"] == author:
                return self._send(422, {"code": "SPONSOR_INVALID"})
            sealed_by_author = sum(1 for s in SEALS.values() if s["author"] == author)
            if sealed_by_author >= SEALS_PER_AUTHOR:
                return self._send(409, {"code": "SHELF_FULL", "limit": SEALS_PER_AUTHOR})
            app_id = f"APP-{_next_app:04d}"
            _next_app += 1
            APPLICATIONS[app_id] = {
                "application_id": app_id,
                "title": title,
                "author": author,
                "year": year,
                "sponsor_seal": sponsor,
                "state": "pending",
                "ticks_in_state": 0,
            }
            return self._send(202, APPLICATIONS[app_id])

        if path == "/v1/tick":
            for app in APPLICATIONS.values():
                if app["state"] in ("sealed", "lapsed"):
                    continue
                app["ticks_in_state"] += 1
                if app["state"] == "pending" and app["ticks_in_state"] > ATTEST_DEADLINE_TICKS:
                    app["state"] = "lapsed"
            return self._send(200, {"applications": list(APPLICATIONS.values())})

        if path.startswith("/v1/applications/") and path.endswith("/attest"):
            app = APPLICATIONS.get(path.split("/")[3])
            if app is None:
                return self._send(404, {"code": "UNKNOWN_APPLICATION"})
            if app["state"] != "pending":
                return self._send(409, {"code": "WRONG_STATE", "state": app["state"]})
            if body.get("phrase") != OATH:
                return self._send(403, {"code": "OATH_MISMATCH"})
            app["state"] = "provisional"
            app["ticks_in_state"] = 0
            return self._send(200, app)

        if path.startswith("/v1/applications/") and path.endswith("/seal"):
            app = APPLICATIONS.get(path.split("/")[3])
            if app is None:
                return self._send(404, {"code": "UNKNOWN_APPLICATION"})
            if app["state"] != "provisional":
                return self._send(409, {"code": "WRONG_STATE", "state": app["state"]})
            if app["ticks_in_state"] < PROBATION_TICKS:
                remaining = PROBATION_TICKS - app["ticks_in_state"]
                return self._send(425, {"code": "TOO_EARLY", "ticks_remaining": remaining})
            code = seal_for(app["author"], app["year"])
            SEALS[code] = {"title": app["title"], "author": app["author"], "year": app["year"]}
            app["state"] = "sealed"
            app["seal"] = code
            return self._send(201, {"seal": code, **app})

        return self._send(404, {"code": "NO_SUCH_ROUTE"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    seed()
    print(f"OIR mock listening on http://127.0.0.1:{args.port} (seeded seals: {', '.join(SEALS)})")
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
