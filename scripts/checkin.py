#!/usr/bin/env python3
"""Log a beer. The whole point of M2 (NVB-80): start collecting now.

The binding constraint from docs/09 is **under 30 seconds, one-handed, in a
noisy bar**. So every prompt takes digits or Enter, nothing needs typing, and
every step after the rating is skippable with Enter.

    python scripts/checkin.py            # log one
    python scripts/checkin.py --list     # what's been logged
    python scripts/checkin.py --at 2026-08-29T21:00   # backfill

ponytail: a terminal prompt, not an app. docs/09 wants a phone eventually, but
a UI built before there is data is the classic way to spend three months and
learn nothing (ROADMAP, "deliberately not on the roadmap"). The store is the
part that has to be right; the front end is replaceable.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, datetime

from taam.storage import db

CHIPS = ["bitter", "sweet", "sour", "malty", "fruity", "roasty", "boozy", "watery",
         "nothing much"]

# The bootstrap set (D-009 option B): fixed, so answers stay comparable. Bump the
# version if the wording changes — a reworded question is not the same question.
QUESTIONS: list[tuple[str, int, str, list[str], bool]] = [
    ("stood_out", 1, "what stood out?", CHIPS, True),
    ("too_much", 1, "too much of anything?", CHIPS, True),
    ("another_now", 1, "another right now?", ["yes", "no", "one was enough"], False),
]

TAG_CHIPS = ["with-food", "friends", "alone", "outdoors", "bar", "home", "hot-day"]


def parse_picks(text: str, options: list[str], multi: bool) -> list[str]:
    """'1 4' or '1,4' -> the chosen chips. Unknown numbers are ignored, not fatal:
    a fat-fingered digit in a bar must not cost the whole check-in."""
    picks = [options[i - 1] for tok in text.replace(",", " ").split()
             if tok.isdigit() and 1 <= (i := int(tok)) <= len(options)]
    seen = dict.fromkeys(picks)  # de-dup, keep order
    return list(seen)[: None if multi else 1]


def ask(prompt: str, options: list[str], multi: bool) -> list[str]:
    menu = "  ".join(f"{n}={o}" for n, o in enumerate(options, 1))
    return parse_picks(input(f"{prompt}\n  {menu}\n  > "), options, multi)


def ask_rating() -> float | None:
    """0–10, per D-010 option B. Re-asks on garbage rather than accepting None:
    the rating is the target variable, so silently dropping it costs a whole
    check-in's worth of signal for one mistyped character."""
    while True:
        raw = input("  rating 0-10 (Enter to skip) > ").strip()
        if not raw:
            return None
        try:
            rating = float(raw)
        except ValueError:
            print("  a number, 0 to 10")
            continue
        if 0 <= rating <= 10:
            return rating
        print("  0 to 10")


def pick_item(con: sqlite3.Connection, at: datetime) -> int:
    recent = db.recent_items(con)
    for n, r in enumerate(recent, 1):
        print(f"  {n}. {r['name']}" + (f" — {r['maker']}" if r["maker"] else ""))
    raw = input("  beer (number, or type a name) > ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(recent):
        return int(recent[int(raw) - 1]["id"])
    if not raw:
        sys.exit("nothing entered")

    hits = db.search_items(con, raw)
    if hits:
        for n, r in enumerate(hits, 1):
            print(f"  {n}. {r['name']}" + (f" — {r['maker']}" if r["maker"] else ""))
        sel = input(f"  number, or Enter to add '{raw}' as new > ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(hits):
            return int(hits[int(sel) - 1]["id"])

    maker = input("  brewery (Enter to skip) > ").strip()
    style = input("  style   (Enter to skip) > ").strip()
    abv = input("  abv %   (Enter to skip) > ").strip()
    return db.find_or_create_item(
        con, raw, maker=maker or None, style=style or None,
        abv=float(abv) if abv.replace(".", "", 1).isdigit() else None,
        retrieved_at=at.isoformat(timespec="seconds"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--list", action="store_true", help="show recent check-ins and exit")
    p.add_argument("--at", help="when it was drunk, ISO (default: now)")
    p.add_argument("--db", help="database path (default: data/taam.db, or $TAAM_DB)")
    args = p.parse_args()

    con = db.connect(args.db)

    if args.list:
        rows = con.execute(
            """SELECT c.at, c.rating, i.name, i.maker FROM checkin c
               JOIN item i ON i.id = c.item_id ORDER BY c.at DESC LIMIT 30""").fetchall()
        for r in rows:
            maker = f" — {r['maker']}" if r["maker"] else ""
            rating = "-" if r["rating"] is None else r["rating"]  # 0 is a real rating
            print(f"{r['at'][:16]}  {rating!s:>4}/10  {r['name']}{maker}")
        print(f"\n{con.execute('SELECT COUNT(*) FROM checkin').fetchone()[0]} check-ins")
        return 0

    at = (datetime.fromisoformat(args.at) if args.at else datetime.now(UTC)).astimezone()
    item_id = pick_item(con, at)

    rating = ask_rating()

    answers = [(qid, ver, picks if multi else (picks[0] if picks else None))
               for qid, ver, text, opts, multi in QUESTIONS
               for picks in [ask(f"  {text}", opts, multi)]]

    suggested = db.last_tags(con) or [db.time_of_day(at)]
    print(f"  context — Enter keeps {suggested}")
    tags = ask("  tags", TAG_CHIPS, True) or suggested
    if db.time_of_day(at) not in tags:
        tags = [*tags, db.time_of_day(at)]

    notes = input("  notes (Enter to skip) > ").strip()

    cid = db.add_checkin(con, item_id, rating, answers, tags, notes, at=at)
    item = con.execute("SELECT name FROM item WHERE id = ?", (item_id,)).fetchone()
    print(f"\nlogged #{cid}  {item['name']}  {rating if rating is not None else '-'}/10  {tags}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        # Nothing is written until the last prompt, so a bailout loses only
        # this check-in. Say so plainly instead of printing a traceback.
        raise SystemExit("\naborted, nothing logged") from None
