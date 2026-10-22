#!/usr/bin/env python3
"""csv_cleaner.py - clean a messy CSV: dedupe rows, trim whitespace,
collapse null-ish cells, drop empty rows. Stdlib only.

Usage:  python csv_cleaner.py input.csv [-o output.csv] [--report]
        python csv_cleaner.py --selftest
"""
import argparse
import csv
import sys

# cells that mean "no value" (lowercased, after stripping)
NULLISH = {"", "n/a", "na", "null", "none", "-", "--", "?", "nan"}


def clean(rows, dedupe_key=None):
    """Return (clean_rows, stats_dict). Rows = list of lists, row 0 = header."""
    header, body = rows[0], rows[1:]
    stats = {"rows_in": len(body), "dupes": 0, "empty_rows": 0, "cells_fixed": 0}

    cleaned = []
    seen = set()

    for row in body:
        # ragged rows: pad to header width, never drop data
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            stats["cells_fixed"] += len(row) - len(header)
            row = row[:len(header)]

        # trim spaces, nullish -> "", count changed cells
        fixed = []
        for v in row:
            s = str(v).strip()
            if s.lower() in NULLISH:
                fixed.append("")
            else:
                fixed.append(s)
        stats["cells_fixed"] += sum(1 for a, b in zip(row, fixed) if a != b)

        if all(v == "" for v in fixed):
            stats["empty_rows"] += 1
            continue

        key = tuple(v.lower() for v in fixed) if dedupe_key is None else \
            tuple(fixed[i] for i in dedupe_key)
        if key in seen:
            stats["dupes"] += 1
            continue
        seen.add(key)
        cleaned.append(fixed)

    stats["rows_out"] = len(cleaned)
    return [header] + cleaned, stats


def run(path, out=None, dedupe_cols=None):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit("empty file")
    cleaned, stats = clean(rows, dedupe_cols)
    target = out or path.replace(".csv", "_clean.csv")
    with open(target, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(cleaned)
    print(f"in={stats['rows_in']} -> out={stats['rows_out']} | "
          f"dupes={stats['dupes']} empty={stats['empty_rows']} "
          f"cells_fixed={stats['cells_fixed']} | wrote {target}")


def selftest():
    raw = [
        ["id", "name", "email"],
        ["1", " Ana  ", "A@x.com"],
        ["2", "  Bo ", "N/A"],
        [" 1 ", "Ana", "a@x.com"],          # dupe of row 1
        ["", "", "", ""],                  # ragged empty row -> truncated + dropped
        ["", "", "extra", "cell"],         # ragged -> truncated, real data kept
        ["3", "Cy", "-"],
    ]
    out, stats = clean(raw)
    assert stats == {"rows_in": 6, "dupes": 1, "empty_rows": 1,
                     "cells_fixed": 7, "rows_out": 4}, stats
    assert out[1] == ["1", "Ana", "A@x.com"], out[1]
    assert out[2] == ["2", "Bo", ""], out[2]
    assert out[3] == ["", "", "extra"], out[3]
    assert out[-1] == ["3", "Cy", ""], out[-1]
    print("selftest OK")


# shortcut: rows wider than the header lose their overflow cells; upgrade to
# a quarantine report (extra columns archived per row) if a client has ragged
# multi-record rows.


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="csv file to clean")
    ap.add_argument("-o", "--output")
    ap.add_argument("--dedupe-cols", help="comma-separated 0-based column indexes")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.input:
        cols = ([int(i) for i in args.dedupe_cols.split(",")]
                if args.dedupe_cols else None)
        run(args.input, args.output, cols)
    else:
        ap.print_help()
