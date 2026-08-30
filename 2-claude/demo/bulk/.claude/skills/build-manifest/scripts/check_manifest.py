#!/usr/bin/env python3
"""Validate an Ondura bulk manifest (.man) file.

    check_manifest.py manifests/20260814.man

Prints one line per problem and exits 1 if any were found; prints "OK" and
exits 0 otherwise. Python 3.8 compatible, standard library only.
"""

import sys
from typing import List

HEADER_LEN = 26
RECORD_LEN = 79
TRAILER_LEN = 10
MAGIC = "OIRBULK1"
DISPOSITIONS = ("LN", "RS", "WD")
CHECK_ALPHABET = "BCDFGHJKLMNPQRSTVWXZ"
MODULUS = 999983


def checksum(record_lines: List[str]) -> str:
    total = 0
    for index, line in enumerate(record_lines, start=1):
        total += sum(ord(c) for c in line) * index
    return "{:06d}".format(total % MODULUS)


def check_char(shelf: str, year: str) -> str:
    total = sum(int(d) for d in year) + sum(ord(c) - 64 for c in shelf)
    return CHECK_ALPHABET[(total * 7) % 20]


def validate(path: str) -> List[str]:
    problems = []
    with open(path, "rb") as handle:
        raw = handle.read()

    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        return ["non-ASCII byte at offset {}".format(error.start)]

    if b"\r\n" not in raw:
        problems.append("line endings must be CRLF")
    if not raw.endswith(b"\r\n"):
        problems.append("file must end with CRLF")
    if raw.endswith(b"\r\n\r\n"):
        problems.append("no blank line after the trailer")

    lines = text.split("\r\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) < 2:
        return problems + ["file must have a header and a trailer"]

    header, trailer = lines[0], lines[-1]
    records = lines[1:-1]

    if len(header) != HEADER_LEN:
        problems.append("header is {} chars, expected {}".format(len(header), HEADER_LEN))
    if not header.startswith(MAGIC):
        problems.append("header must start with " + MAGIC)
    if len(header) == HEADER_LEN:
        declared = header[16:20]
        if not declared.isdigit() or int(declared) != len(records):
            problems.append("header count {} != {} records".format(declared, len(records)))
        expected = checksum(records)
        if header[20:26] != expected:
            problems.append("checksum is {}, expected {}".format(header[20:26], expected))

    if not trailer.startswith("OIREND") or len(trailer) != TRAILER_LEN:
        problems.append("trailer must be OIREND + 4-digit count")
    elif trailer[6:10].isdigit() and int(trailer[6:10]) != len(records):
        problems.append("trailer count {} != {} records".format(trailer[6:10], len(records)))

    for number, line in enumerate(records, start=1):
        where = "record {}".format(number)
        if len(line) != RECORD_LEN:
            problems.append("{}: {} chars, expected {}".format(where, len(line), RECORD_LEN))
            continue
        sequence, seal, title, disposition = line[:6], line[6:13], line[13:77], line[77:79]
        if not sequence.isdigit() or int(sequence) != number:
            problems.append("{}: sequence is {}, expected {:06d}".format(where, sequence, number))
        if title != title.rstrip() + " " * (64 - len(title.rstrip())):
            problems.append("{}: title must be left-aligned and space-padded".format(where))
        if disposition not in DISPOSITIONS:
            problems.append("{}: disposition {!r} not in {}".format(where, disposition, DISPOSITIONS))
        shelf, year, check = seal[:2], seal[2:6], seal[6]
        if not (shelf.isalpha() and shelf.isupper() and year.isdigit()):
            problems.append("{}: seal {!r} is not a compact code".format(where, seal))
        elif check_char(shelf, year) != check:
            problems.append(
                "{}: seal {} has check character {}, expected {}".format(
                    where, seal, check, check_char(shelf, year)))
    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    problems = validate(sys.argv[1])
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
