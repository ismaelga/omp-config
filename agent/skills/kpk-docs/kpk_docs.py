#!/usr/bin/env python3
"""Query docs.kpk.io without MCP: index lookup, parallel page fetch, ask endpoint.

Usage:
  kpk_docs.py fetch <url> [<url> ...]          # fetch one or more .md pages (parallel)
  kpk_docs.py index [regex]                    # list llms.txt entries, optional filter
  kpk_docs.py ask <page-url> <question> [goal] # ask endpoint on a page

Exit 0 on success; non-zero on HTTP/parse errors. All requests run in parallel
via asyncio.to_thread.
"""

import argparse
import asyncio
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://docs.kpk.io"
UA = "omp-kpk-docs-script/1.0"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


async def fetch_many(urls: list[str]) -> list[str]:
    return await asyncio.gather(*[asyncio.to_thread(_fetch, u) for u in urls])


def cmd_fetch(args) -> int:
    pages = asyncio.run(fetch_many(args.urls))
    for url, page in zip(args.urls, pages):
        print(f"===== {url} =====")
        print(page)
    return 0


def cmd_index(args) -> int:
    text = _fetch(f"{BASE}/llms.txt")
    pat = re.compile(args.regex or "", re.I)
    for line in text.splitlines():
        if line.startswith("- [") and pat.search(line):
            print(line)
    return 0


def cmd_ask(args) -> int:
    q = urllib.parse.quote(args.question)
    url = f"{args.page}?ask={q}"
    if args.goal:
        url += f"&goal={urllib.parse.quote(args.goal)}"
    print(_fetch(url))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="fetch .md pages in parallel")
    pf.add_argument("urls", nargs="+")
    pf.set_defaults(func=cmd_fetch)

    pi = sub.add_parser("index", help="list llms.txt entries (optional regex filter)")
    pi.add_argument("regex", nargs="?")
    pi.set_defaults(func=cmd_index)

    pa = sub.add_parser("ask", help="ask endpoint on a page URL")
    pa.add_argument("page", help="page URL, e.g. https://docs.kpk.io/readme.md")
    pa.add_argument("question")
    pa.add_argument("goal", nargs="?")
    pa.set_defaults(func=cmd_ask)

    args = p.parse_args()
    try:
        return args.func(args)
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"network error: {e.reason}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())