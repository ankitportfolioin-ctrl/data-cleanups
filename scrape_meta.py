#!/usr/bin/env python3
"""scrape_meta.py - extract title + meta tags from a web page.
Stdlib only (urllib + html.parser). Polite: sets a UA, 15s timeout,
and prints what it got without crashing on messy HTML.

Usage:  python scrape_meta.py <url> [--csv out.csv]
        python scrape_meta.py --selftest
"""
import argparse
import csv
import sys
from html.parser import HTMLParser
from urllib import request
from urllib.error import URLError

WANTED = {"title", "description", "og:title", "og:description", "og:image"}
UA = "Mozilla/5.0 (compatible; MetaBot/1.0; +contact-available-on-request)"


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("name") or a.get("property") or ""
            key = key.lower()
            if key in WANTED and a.get("content", "").strip():
                self.meta[key] = a["content"].strip()
        elif tag == "title":
            self._in_title = True

    def handle_data(self, data):
        if getattr(self, "_in_title", False):
            t = data.strip()
            if t:
                self.meta["title"] = self.meta.get("title", "") + t

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def parse(html_text):
    p = MetaParser()
    p.feed(html_text)
    p.close()
    return p.meta


def fetch(url):
    req = request.Request(url, headers={"User-Agent": UA})
    with request.urlopen(req, timeout=15) as r:
        # respect ISO-8859-1 default when no charset given (RFC rules)
        charset = r.headers.get_content_charset() or "latin-1"
        return r.read().decode(charset, errors="replace")


def selftest():
    html = """<html><head><title>  Test Shop  </title>
    <meta name="description" content="Cheap widgets. ">
    <meta name="keywords" content="ignore me">
    <meta property="og:title" content="Test Shop — Widgets">
    <meta property="og:description" content=" Widget deals all week ">
    </head><body><h1>widgets!</h1></body></html>"""
    m = parse(html)
    assert m["title"] == "Test Shop", m
    assert m["description"] == "Cheap widgets.", m
    assert m["og:title"] == "Test Shop — Widgets", m
    assert m["og:description"] == "Widget deals all week", m
    assert "keywords" not in m, m  # only wanted keys
    print("selftest OK (no network used)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--csv", help="append results to this csv")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.url:
        ap.print_help()
        return
    try:
        meta = parse(fetch(args.url))
    except (URLError, OSError, ValueError) as e:
        sys.exit(f"fetch failed: {e}")
    print(args.url)
    for k in sorted(WANTED | {"title"}):
        if k in meta:
            print(f"  {k}: {meta[k]}")
    if args.csv:
        new = not __import__("os").path.exists(args.csv)
        with open(args.csv, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["url"] + sorted(WANTED | {"title"}))
            w.writerow([args.url] + [meta.get(k, "") for k in sorted(WANTED | {"title"})])
        print(f"appended to {args.csv}")


if __name__ == "__main__":
    main()
