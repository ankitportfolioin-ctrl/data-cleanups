# data-cleanups

Small, zero-dependency Python tools for common data-cleanup jobs.
No pip installs, no virtualenv, no internet needed — each file runs standalone
on any Python 3.10+ (Windows / macOS / Linux). Every tool has a `--selftest`.

## csv_cleaner.py
Dedupes rows, trims whitespace, normalizes null-ish cells (`N/A`, `NULL`, `-`...)
to true empties, fixes ragged rows, drops empty rows, and prints a before/after
report. Your original file is never modified.

```
python csv_cleaner.py messy.csv          # -> messy_clean.csv
python csv_cleaner.py messy.csv -o clean.csv
python csv_cleaner.py --selftest
```

## dupe_finder.py
Finds duplicate files by content (SHA-256, size-first fast path) anywhere in a
folder tree. **Read-only:** it reports what could be deleted, it never deletes.

```
python dupe_finder.py C:\Users\you\Downloads --ext jpg,png,csv
python dupe_finder.py --selftest
```

## scrape_meta.py
Grabs `<title>` + meta/OG tags from a page (or 100 pages into a CSV) —
handy for SEO audits, e-commerce listing checks, lead enrichment.

```
python scrape_meta.py https://example.com
python scrape_meta.py https://shop.com/item --csv results.csv
python scrape_meta.py --selftest
```

## Why zero-dependency
These are sold as freelance deliverables: the client must be able to run the
file the day it lands in their inbox, without a tech-support call.

License: MIT
