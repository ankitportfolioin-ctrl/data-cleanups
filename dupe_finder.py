#!/usr/bin/env python3
"""dupe_finder.py - find duplicate files in a folder tree. Read-only
(it reports, it NEVER deletes). Stdlib only.

Duplicates = identical content (SHA-256), regardless of name.
Fast path: group by size first, hash only candidates.

Usage:  python dupe_finder.py <folder> [--ext jpg,csv]
        python dupe_finder.py --selftest
"""
import argparse
import hashlib
import os
import sys
from collections import defaultdict

CHUNK = 1 << 16


def find_dupes(root, exts=None):
    """Return list of duplicate groups; each group is (size, [paths])."""
    exts = {e.lower().lstrip(".") for e in exts} if exts else None
    by_size = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            p = os.path.join(dirpath, name)
            if exts and not name.lower().split(".")[-1] in exts:
                continue

            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            if size == 0:
                continue  # every empty file "matches"; never useful to report
            by_size[size].append(p)

    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for p in paths:
            h = hashlib.sha256()
            try:
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(CHUNK), b""):
                        h.update(chunk)
            except OSError:
                continue
            by_hash[h.hexdigest()].append(p)
        for paths2 in by_hash.values():
            if len(paths2) > 1:
                groups.append((size, paths2))
    groups.sort(key=lambda g: (-g[0] * len(g[1])))  # most wasted bytes first
    return groups


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.txt"); b = os.path.join(d, "b.txt")
        c = os.path.join(d, "c.txt"); e = os.path.join(d, "empty.txt")
        for p, content in ((a, b"hello world"), (b, b"hello world"),
                           (c, b"different"), (e, b"")):
            with open(p, "wb") as f:
                f.write(content)
        groups = find_dupes(d)
        assert len(groups) == 1, groups
        size, paths = groups[0]
        assert set(os.path.basename(p) for p in paths) == {"a.txt", "b.txt"}, paths
        assert size == len(b"hello world"), size
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--ext", help="only these, comma-separated: jpg,csv")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.folder:
        groups = find_dupes(args.folder,
                            exts=args.ext.split(",") if args.ext else None)
        if not groups:
            print("no duplicates found")
        else:
            wasted = 0
            for size, paths in groups:
                keep, copies = paths[0], paths[1:]
                wasted += size * len(copies)
                print(f"\n{size} bytes x{len(paths)}:")
                for p in paths:
                    print(f"  {'KEEP ' if p == keep else 'COPY '}{p}")
            print(f"\n{len(groups)} duplicate group(s), "
                  f"{wasted:,} wasted bytes reclaimable")
    else:
        ap.print_help()
