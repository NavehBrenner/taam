#!/usr/bin/env python3
"""NVB-78 — Is Untappd's `beer_description` populated for Israeli beers?

The last open question in the source strategy, and the one that decides whether
the profiler can run on local beer at all.

Question
--------
catalog.beer was *measured* (NVB-78, 2026-08-30) to carry 10 Israeli beers with
an empty `description` on 10/10 of them, and beer.db carries none at all
(DEAD-ENDS DE-001). Untappd is therefore the last candidate source of prose for
an Israeli beer.

This matters because of how the profiler works: descriptors are never fetched,
they are *predicted* from text (docs/06, D-002 option B). No description means
the regressor has no input. So:

  descriptions are decent   Untappd keeps its narrow gap-filler slot (D-004 A)
  descriptions are thin     NO source has prose for a local beer. D-002 option B
                            cannot run on the local tail, the profiler falls back
                            to an LLM or manual entry for every Israeli beer, and
                            D-004 option D (drop Untappd entirely) becomes the
                            obvious answer — which deletes the whole retention
                            problem in docs/13.

Method
------
For each beer in the sample: `GET /v4/search/beer`, keep the hit whose brewery
matches what we asked for, then `GET /v4/beer/info/{bid}` and record the LENGTH
of `beer_description`. Three outcomes per beer, and the difference between the
last two is the entire point:

  NOT_FOUND       Untappd does not have the beer      (a coverage finding)
  FOUND_NO_DESC   Untappd has it, description empty   (adds nothing over a label)
  FOUND_DESC      Untappd has it, with n characters   (the only useful case)

Interpretation
--------------
  median length >= 100 chars and <50% empty     Untappd earns its slot
  median < 100 chars, or >=50% empty            it does not — see D-004 option D

Terms compliance — read docs/13-scraping-policy.md before touching this
---------------------------------------------------------------------
  * Documented API only (§10.2). This is not a scraper and must never become
    one; reading beer pages directly is forbidden by §10.1.
  * ~2 calls per beer, ~40 for the default sample, against a 100/hour limit.
  * NOTHING IS PERSISTED BUT LENGTHS. Untappd's terms require cache purges every
    24h, and the prose is the copyrightable part (§3). Descriptions are printed
    for your eyes and then dropped; only integer lengths reach --out. That is
    also what makes the result publishable in a public repo.
  * Data via the Untappd API. Attribution required by their terms.

Usage
-----
    # credentials from https://untappd.com/api/register (needs a login)
    export UNTAPPD_CLIENT_ID=... UNTAPPD_CLIENT_SECRET=...
    python scripts/untappd_description_check.py

    # or put them in .env (gitignored) and just run it
    python scripts/untappd_description_check.py --out docs/data/untappd-il-check.md

    # prove the verdict logic works, no network and no key needed:
    python scripts/untappd_description_check.py --self-test
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # `requests` is a real dependency; this keeps --self-test import-free
    import requests

API = "https://api.untappd.com/v4"

# The sample. Chosen to span the breweries NVB-78 checked against catalog.beer,
# so the two sources are measured on the same shelf. Import-only brands are
# excluded on purpose: the question is about the LOCAL tail, which is precisely
# where user-created entries are expected to be thin.
SAMPLE: list[tuple[str, str]] = [
    ("Tempo", "Goldstar"),
    ("Tempo", "Maccabee"),
    ("Alexander", "Alexander Blonde"),
    ("Alexander", "Alexander Amber"),
    ("Alexander", "Alexander Black"),
    ("Malka", "Malka Blonde"),
    ("Malka", "Malka Pale Ale"),
    ("Malka", "Malka Stout"),
    ("Jem's", "Jem's Pilsner"),
    ("Jem's", "Jem's Amber"),
    ("Jem's", "Jem's 8.8"),
    ("Negev", "Negev Porter"),
    ("Negev", "Negev Amber"),
    ("Shapiro", "Shapiro Pale Ale"),
    ("Shapiro", "Shapiro IPA"),
    ("Shapiro", "Shapiro Stout"),
    ("Beer Bazaar", "Beer Bazaar Hipster Ale"),
    ("Herzl", "Herzl Vision"),
    ("Bazelet", "Bazelet Blonde"),
    ("Sheeta", "Sheeta Blonde"),
]

# Below this, a "description" is a style tag or a slogan, not something a
# regressor can learn from. Stated up front so the verdict is not tuned to the
# result after seeing it.
USEFUL_CHARS = 100


@dataclass
class Result:
    """One beer's outcome. Deliberately holds no description text."""

    brewery: str
    query: str
    outcome: str  # NOT_FOUND | FOUND_NO_DESC | FOUND_DESC
    matched_beer: str = ""
    matched_brewery: str = ""
    bid: int = 0
    desc_chars: int = 0


def _get(session: requests.Session, path: str, params: dict[str, str]) -> dict[str, Any]:
    """One documented-API call. Raises on anything that is not a clean 200."""
    resp = session.get(f"{API}/{path}", params=params, timeout=30)
    if resp.status_code == 429:
        raise SystemExit(
            "Untappd returned 429: the 100/hour limit is exhausted. Wait an hour "
            "and re-run — do not work around this, see docs/13 §10.2."
        )
    resp.raise_for_status()
    body: dict[str, Any] = resp.json()
    return body


def check_beer(
    session: requests.Session, brewery: str, query: str, creds: dict[str, str]
) -> Result:
    """Search for one beer, then fetch its description length.

    The brewery match is what stops us scoring a US beer with a similar name —
    the exact failure that made catalog.beer look twice as covered as it is.
    """
    found = _get(session, "search/beer", {**creds, "q": query, "limit": "5"})
    items = found.get("response", {}).get("beers", {}).get("items", [])

    hit = None
    for item in items:
        name = item.get("brewery", {}).get("brewery_name", "")
        if brewery.lower().replace("'", "") in name.lower().replace("'", ""):
            hit = item
            break
    if hit is None:
        return Result(brewery=brewery, query=query, outcome="NOT_FOUND")

    bid = int(hit["beer"]["bid"])
    info = _get(session, f"beer/info/{bid}", {**creds, "compact": "true"})
    beer = info.get("response", {}).get("beer", {})
    description = (beer.get("beer_description") or "").strip()

    # Printed for the human, then dropped. Never written to --out. See docs/13 §3.
    if description:
        preview = description[:110].replace("\n", " ")
        print(f"      ↳ {preview}{'…' if len(description) > 110 else ''}", file=sys.stderr)

    return Result(
        brewery=brewery,
        query=query,
        outcome="FOUND_DESC" if description else "FOUND_NO_DESC",
        matched_beer=str(beer.get("beer_name", hit["beer"].get("beer_name", ""))),
        matched_brewery=str(hit.get("brewery", {}).get("brewery_name", "")),
        bid=bid,
        desc_chars=len(description),
    )


def verdict(results: list[Result]) -> tuple[str, str]:
    """Return (verdict, reasoning). Thresholds are fixed in USEFUL_CHARS above."""
    if not results:
        return "NO DATA", "nothing was checked"

    found = [r for r in results if r.outcome != "NOT_FOUND"]
    if not found:
        return (
            "UNTAPPD ADDS NOTHING",
            f"0 of {len(results)} sampled beers exist on Untappd at all",
        )

    lengths = [r.desc_chars for r in found]
    median = statistics.median(lengths)
    empty = sum(1 for r in found if r.desc_chars == 0)
    empty_frac = empty / len(found)

    if median >= USEFUL_CHARS and empty_frac < 0.5:
        return (
            "UNTAPPD EARNS ITS SLOT",
            (
                f"median {median:.0f} chars over {len(found)} found beers, "
                f"{empty_frac:.0%} empty — real prose exists for local beer, so "
                "D-004 option A (narrow gap-filler) stands"
            ),
        )
    return (
        "UNTAPPD ADDS NOTHING",
        (
            f"median {median:.0f} chars over {len(found)} found beers, "
            f"{empty_frac:.0%} empty — below the {USEFUL_CHARS}-char bar. No source "
            "has prose for a local beer: D-002 option B cannot run on the local "
            "tail, and D-004 option D (drop Untappd) becomes the obvious answer"
        ),
    )


def render(results: list[Result]) -> str:
    """Markdown summary. Lengths only — no description text, by design."""
    lines = [
        "| Brewery | Queried | Outcome | Matched | Description chars |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        matched = f"{r.matched_beer} ({r.matched_brewery})" if r.matched_beer else "—"
        chars = str(r.desc_chars) if r.outcome == "FOUND_DESC" else "—"
        lines.append(f"| {r.brewery} | {r.query} | {r.outcome} | {matched} | {chars} |")

    found = [r for r in results if r.outcome != "NOT_FOUND"]
    call, why = verdict(results)
    with_desc = sum(1 for r in found if r.desc_chars > 0)
    lines += [
        "",
        (
            f"- sampled: **{len(results)}**, found on Untappd: **{len(found)}**, "
            f"with a description: **{with_desc}**"
        ),
        f"- **Verdict: {call}** — {why}",
        "",
        (
            "Description *lengths* only. The text itself is never stored: Untappd's "
            "terms require cache purges every 24h and the prose is the copyrightable "
            "part (`docs/13-scraping-policy.md` §3). Data via the Untappd API."
        ),
    ]
    return "\n".join(lines)


def self_test() -> int:
    """Two controls, mirroring the M0 harness: can it detect prose, and can it
    refuse to endorse the absence of prose? A verdict function that only ever
    says one thing is worthless, so both directions are asserted."""
    rich = [
        Result("B", f"b{i}", "FOUND_DESC", "x", "B", i, 240)
        for i in range(10)
    ]
    call, _ = verdict(rich)
    assert call == "UNTAPPD EARNS ITS SLOT", call

    # the expected-but-must-not-be-assumed case: found, but nothing in the field
    barren = [Result("B", f"b{i}", "FOUND_NO_DESC", "x", "B", i, 0) for i in range(10)]
    call, _ = verdict(barren)
    assert call == "UNTAPPD ADDS NOTHING", call

    # a style tag is not a description
    tags = [Result("B", f"b{i}", "FOUND_DESC", "x", "B", i, 22) for i in range(10)]
    call, _ = verdict(tags)
    assert call == "UNTAPPD ADDS NOTHING", call

    # half empty, half rich: still fails, because half the catalog is unusable
    mixed = [Result("B", f"b{i}", "FOUND_DESC", "x", "B", i, 400) for i in range(5)]
    mixed += [Result("B", f"c{i}", "FOUND_NO_DESC", "x", "B", i, 0) for i in range(5)]
    call, _ = verdict(mixed)
    assert call == "UNTAPPD ADDS NOTHING", call

    # absent entirely is a distinct, reportable outcome
    call, why = verdict([Result("B", "b", "NOT_FOUND") for _ in range(5)])
    assert call == "UNTAPPD ADDS NOTHING" and "exist on Untappd" in why, why

    assert "beer_description" not in render(rich)
    print("self-test passed: the verdict detects prose AND refuses to endorse its absence")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write the markdown summary here")
    parser.add_argument("--self-test", action="store_true", help="no network, no key")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    try:
        import requests
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dependency is in requirements.txt
        print("pip install -r requirements.txt", file=sys.stderr)
        return 1

    load_dotenv()
    client_id = os.environ.get("UNTAPPD_CLIENT_ID", "")
    client_secret = os.environ.get("UNTAPPD_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print(
            "Need UNTAPPD_CLIENT_ID and UNTAPPD_CLIENT_SECRET (env or .env).\n"
            "Register an app at https://untappd.com/api/register (requires a login).\n"
            "No key yet? Run --self-test to check the harness itself.",
            file=sys.stderr,
        )
        return 2
    creds = {"client_id": client_id, "client_secret": client_secret}

    session = requests.Session()
    results = []
    for i, (brewery, query) in enumerate(SAMPLE, 1):
        print(f"[{i:>2}/{len(SAMPLE)}] {query}", file=sys.stderr)
        results.append(check_beer(session, brewery, query, creds))
        time.sleep(1)  # 2 calls/beer against 100/hour; no reason to rush it

    summary = render(results)
    print("\n" + summary)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(summary + "\n")
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
