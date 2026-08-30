#!/usr/bin/env python3
"""Ondura Interlibrary Registry, exposed as an MCP server over stdio.

The same registry the `oir-registration` skill drives through a CLI, offered
instead as typed tools. Standard library only — JSON-RPC over stdin/stdout is
the whole protocol, and reading this file is a decent way to see that.

    python3 mcp/oir_mcp_server.py        # speaks MCP on stdin/stdout

Never write logs to stdout: stdout is the protocol channel. Use stderr.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("OIR_URL", "http://127.0.0.1:8787")
OATH = "By quill and lamplight, I petition Ondura"
SUPPORTED = ("2025-06-18", "2025-03-26", "2024-11-05")

TOOLS = [
    {
        "name": "health",
        "description": "Check whether the Ondura registry is reachable. Call this first; "
                       "if it fails, report that the registry is down rather than guessing.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "verify_seal",
        "description": "Look up a seal code (e.g. OIR-HR-1965-M) and return the book it "
                       "belongs to. Use it to confirm a sponsor exists and to read its author.",
        "inputSchema": {
            "type": "object",
            "properties": {"seal": {"type": "string", "description": "Seal code, OIR-XX-YYYY-C"}},
            "required": ["seal"],
        },
    },
    {
        "name": "list_applications",
        "description": "List every open application with its state and ticks_in_state.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "apply",
        "description": "Open an application for a book. The sponsor must be the seal of an "
                       "already-sealed book by a DIFFERENT author. Returns an application_id; "
                       "the application must then be attested within 2 ticks or it lapses.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "maxLength": 64},
                "author": {"type": "string"},
                "year": {"type": "integer", "minimum": 1450},
                "sponsor_seal": {"type": "string", "description": "Seal of a book by another author"},
            },
            "required": ["title", "author", "year", "sponsor_seal"],
        },
    },
    {
        "name": "attest",
        "description": "Swear the oath for a pending application, moving it to provisional. "
                       "Do this immediately after apply — the pending window is 2 ticks.",
        "inputSchema": {
            "type": "object",
            "properties": {"application_id": {"type": "string"}},
            "required": ["application_id"],
        },
    },
    {
        "name": "tick",
        "description": "Advance the registry clock by one tick, for EVERY open application. "
                       "Probation is 3 ticks. Never tick while an application is pending its "
                       "oath: it will lapse.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "request_seal",
        "description": "Request the permanent seal after 3 ticks of probation. TOO_EARLY is a "
                       "countdown, not a failure.",
        "inputSchema": {
            "type": "object",
            "properties": {"application_id": {"type": "string"}},
            "required": ["application_id"],
        },
    },
]

ROUTES = {
    "health": lambda a: ("GET", "/v1/health", None),
    "verify_seal": lambda a: ("GET", "/v1/seals/{}".format(a["seal"]), None),
    "list_applications": lambda a: ("GET", "/v1/applications", None),
    "apply": lambda a: ("POST", "/v1/applications", {
        "title": a["title"], "author": a["author"],
        "year": a["year"], "sponsor_seal": a["sponsor_seal"]}),
    "attest": lambda a: ("POST", "/v1/applications/{}/attest".format(a["application_id"]),
                         {"phrase": OATH}),
    "tick": lambda a: ("POST", "/v1/tick", {}),
    "request_seal": lambda a: ("POST", "/v1/applications/{}/seal".format(a["application_id"]), {}),
}


def call_registry(method: str, path: str, body):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return False, response.read().decode()
    except urllib.error.HTTPError as error:
        return True, "HTTP {}\n{}".format(error.code, error.read().decode())
    except urllib.error.URLError as error:
        return True, "registry unreachable at {}: {}".format(BASE, error.reason)


def run_tool(name: str, arguments: dict) -> dict:
    if name not in ROUTES:
        return {"content": [{"type": "text", "text": "unknown tool: " + name}], "isError": True}
    try:
        method, path, body = ROUTES[name](arguments or {})
    except KeyError as missing:
        return {"content": [{"type": "text", "text": "missing argument: {}".format(missing)}],
                "isError": True}
    failed, text = call_registry(method, path, body)
    return {"content": [{"type": "text", "text": text}], "isError": failed}


def handle(message: dict):
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        wanted = (message.get("params") or {}).get("protocolVersion")
        return {
            "protocolVersion": wanted if wanted in SUPPORTED else SUPPORTED[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "oir", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = message.get("params") or {}
        return run_tool(params.get("name", ""), params.get("arguments") or {})
    if method == "ping":
        return {}
    if request_id is None:
        return None                      # a notification we don't care about
    raise LookupError(method)


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        request_id = message.get("id")
        try:
            result = handle(message)
        except LookupError as unknown:
            if request_id is not None:
                reply = {"jsonrpc": "2.0", "id": request_id,
                         "error": {"code": -32601, "message": "method not found: {}".format(unknown)}}
                sys.stdout.write(json.dumps(reply) + "\n")
                sys.stdout.flush()
            continue
        if request_id is None or result is None:
            continue                     # notifications get no reply
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
