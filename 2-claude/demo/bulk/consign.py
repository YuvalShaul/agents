#!/usr/bin/env python3
"""Build an Ondura bulk consignment manifest from pending.csv.

    python3 consign.py --date 2026-08-14

Writes manifests/<YYYYMMDD>.man. Refuses to overwrite an existing manifest:
manifests are immutable once written (see CLAUDE.md).

Python 3.8 compatible, standard library only — the batch host is old.
"""

import argparse
import csv
import os
from typing import List, Tuple

RECORD_LEN = 79
TITLE_WIDTH = 64
MODULUS = 999983
HERE = os.path.dirname(os.path.abspath(__file__))


def compact(seal: str) -> str:
    """OIR-HR-1965-M -> HR1965M (the wire form used in manifest files)."""
    parts = seal.split("-")
    if len(parts) != 4 or parts[0] != "OIR":
        raise ValueError("not a seal code: {}".format(seal))
    return parts[1] + parts[2] + parts[3]


def read_pending(path: str) -> List[Tuple[str, str, str]]:
    rows = []
    with open(path, newline="", encoding="ascii") as handle:
        for row in csv.reader(handle):
            if not row or row[0].startswith("#"):
                continue
            seal, title, disposition = (field.strip() for field in row)
            rows.append((seal, title, disposition))
    return rows


def build_record(sequence: int, seal: str, title: str, disposition: str) -> str:
    if len(title) > TITLE_WIDTH:
        raise ValueError("title over {} chars: {}".format(TITLE_WIDTH, title))
    record = "{:06d}{}{}{}".format(
        sequence, compact(seal), title.ljust(TITLE_WIDTH), disposition)
    assert len(record) == RECORD_LEN, len(record)
    return record


def checksum(records: List[str]) -> str:
    total = 0
    for index, line in enumerate(records, start=1):
        total += sum(ord(c) for c in line) * index
    return "{:06d}".format(total % MODULUS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD, Ondura Standard Time")
    parser.add_argument("--pending", default=os.path.join(HERE, "pending.csv"))
    args = parser.parse_args()

    stamp = args.date.replace("-", "")
    target = os.path.join(HERE, "manifests", "{}.man".format(stamp))
    if os.path.exists(target):
        print("refusing to overwrite {} — manifests are immutable".format(target))
        return 1

    records = [build_record(i, *row) for i, row in enumerate(read_pending(args.pending), 1)]
    header = "OIRBULK1{}{:04d}{}".format(stamp, len(records), checksum(records))
    trailer = "OIREND{:04d}".format(len(records))

    with open(target, "wb") as handle:
        for line in [header] + records + [trailer]:
            handle.write(line.encode("ascii") + b"\r\n")

    print("wrote {} ({} records)".format(target, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
