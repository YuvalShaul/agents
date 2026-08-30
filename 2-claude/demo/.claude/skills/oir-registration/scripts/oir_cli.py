#!/usr/bin/env python3
"""Client for the Ondura Interlibrary Registry (OIR).

    oir_cli.py health
    oir_cli.py verify OIR-HR-1965-X
    oir_cli.py apply --title "Children of Dune" --author "F. Herbert" \
                     --year 1976 --sponsor OIR-ST-1815-M
    oir_cli.py attest APP-0001
    oir_cli.py status [APP-0001]
    oir_cli.py tick
    oir_cli.py seal APP-0001

Exit code is 0 on a 2xx response and 1 otherwise; the registry's JSON body
is printed either way, so read the `code` field on failure.
Standard library only. Base URL: $OIR_URL, default http://127.0.0.1:8787
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("OIR_URL", "http://127.0.0.1:8787")
OATH = "By quill and lamplight, I petition Ondura"


def call(method: str, path: str, body: dict | None = None) -> int:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            print(response.read().decode())
            return 0
    except urllib.error.HTTPError as error:
        print(f"HTTP {error.code}", file=sys.stderr)
        print(error.read().decode())
        return 1
    except urllib.error.URLError as error:
        print(f"registry unreachable at {BASE}: {error.reason}", file=sys.stderr)
        print("start it with: python3 oir_mock.py", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Ondura Interlibrary Registry client")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health")
    sub.add_parser("tick", help="advance the registry clock by one tick")

    verify = sub.add_parser("verify", help="look up a seal")
    verify.add_argument("seal")

    apply_cmd = sub.add_parser("apply", help="open an application")
    apply_cmd.add_argument("--title", required=True)
    apply_cmd.add_argument("--author", required=True)
    apply_cmd.add_argument("--year", type=int, required=True)
    apply_cmd.add_argument("--sponsor", required=True, help="seal of a book by another author")

    attest = sub.add_parser("attest", help="swear the oath (required while pending)")
    attest.add_argument("application_id")

    status = sub.add_parser("status")
    status.add_argument("application_id", nargs="?")

    seal = sub.add_parser("seal", help="request the seal after probation")
    seal.add_argument("application_id")

    args = parser.parse_args()

    if args.command == "health":
        return call("GET", "/v1/health")
    if args.command == "tick":
        return call("POST", "/v1/tick")
    if args.command == "verify":
        return call("GET", f"/v1/seals/{args.seal}")
    if args.command == "apply":
        return call("POST", "/v1/applications", {
            "title": args.title,
            "author": args.author,
            "year": args.year,
            "sponsor_seal": args.sponsor,
        })
    if args.command == "attest":
        return call("POST", f"/v1/applications/{args.application_id}/attest", {"phrase": OATH})
    if args.command == "status":
        if args.application_id:
            return call("GET", f"/v1/applications/{args.application_id}")
        return call("GET", "/v1/applications")
    if args.command == "seal":
        return call("POST", f"/v1/applications/{args.application_id}/seal", {})
    return 1


if __name__ == "__main__":
    sys.exit(main())
