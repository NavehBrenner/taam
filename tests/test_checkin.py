"""Checks for the check-in store and the chip parser.

    python tests/test_checkin.py        # or: pytest tests/

Two things here are load-bearing and would fail silently if broken:
the identity key (a typo'd re-entry must land on the SAME item, or the repeat
check-ins that measure rating noise never line up), and the chip parser (it runs
on input typed one-handed in a bar and must never lose a check-in to a stray
character).
"""

from __future__ import annotations

import builtins
import importlib.util
import json
import pathlib
from datetime import datetime

from taam.storage import db

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_checkin():
    spec = importlib.util.spec_from_file_location("checkin", ROOT / "scripts" / "checkin.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_parse_picks() -> None:
    ci = _load_checkin()
    opts = ["bitter", "sweet", "malty"]

    assert ci.parse_picks("1 3", opts, True) == ["bitter", "malty"]
    assert ci.parse_picks("1,3", opts, True) == ["bitter", "malty"]
    assert ci.parse_picks("", opts, True) == []
    # a stray character or an out-of-range digit costs that chip, never the check-in
    assert ci.parse_picks("1 x 9 2", opts, True) == ["bitter", "sweet"]
    assert ci.parse_picks("2 2", opts, True) == ["sweet"]
    # single-answer questions take the first pick only
    assert ci.parse_picks("3 1", opts, False) == ["malty"]


def test_ask_rating() -> None:
    """0 must be accepted (it is a real rating) and garbage must be re-asked,
    never silently turned into a null target variable."""
    ci = _load_checkin()

    def scripted(*replies: str):
        it = iter(replies)
        return lambda _prompt="": next(it)

    original = builtins.input
    try:
        builtins.input = scripted("0")
        assert ci.ask_rating() == 0.0, "0 is a real rating, not a skip"
        builtins.input = scripted("")
        assert ci.ask_rating() is None
        builtins.input = scripted("seven", "77", "-1", "7.5")
        assert ci.ask_rating() == 7.5, "garbage and out-of-range are re-asked"
    finally:
        builtins.input = original


def test_identity_key_survives_sloppy_entry() -> None:
    canonical = db.identity_key("Blonde", "Alexander")
    assert db.identity_key(" blonde ", "alexander") == canonical
    assert db.identity_key("Blonde!", "Alexander Brewery") != canonical  # different maker
    assert db.identity_key("Sample", None)  # no maker is still a usable key


def test_time_of_day() -> None:
    at = datetime.fromisoformat
    assert db.time_of_day(at("2026-08-30T02:00")) == "night"
    assert db.time_of_day(at("2026-08-30T09:00")) == "morning"
    assert db.time_of_day(at("2026-08-30T13:00")) == "noon"
    assert db.time_of_day(at("2026-08-30T17:00")) == "afternoon"
    assert db.time_of_day(at("2026-08-30T21:00")) == "evening"


def test_checkin_round_trip() -> None:
    con = db.connect(":memory:")
    first = db.find_or_create_item(con, "Blonde", maker="Alexander", style="Blonde Ale", abv=5.6)

    cid = db.add_checkin(
        con, first, rating=7,
        answers=[("stood_out", 1, ["malty", "sweet"]), ("another_now", 1, "yes")],
        tags=["with-food", "evening"], notes="with a burger",
        at=datetime.fromisoformat("2026-08-29T21:00"))

    row = con.execute("SELECT * FROM checkin WHERE id = ?", (cid,)).fetchone()
    assert row["rating"] == 7
    assert row["at"].startswith("2026-08-29T21:00:00")  # tz-aware, local offset
    assert row["logged_at"] != row["at"], "backfill must stay visible as backfill"

    answers = {r["question_id"]: (r["question_version"], json.loads(r["answer"]))
               for r in con.execute("SELECT * FROM checkin_answer WHERE checkin_id = ?", (cid,))}
    assert answers["stood_out"] == (1, ["malty", "sweet"])
    assert answers["another_now"] == (1, "yes")

    ctx = con.execute("SELECT * FROM checkin_context WHERE checkin_id = ?", (cid,)).fetchone()
    assert json.loads(ctx["tags"]) == ["with-food", "evening"]
    assert ctx["time_of_day"] == "evening"
    assert db.last_tags(con) == ["with-food", "evening"]

    # The same beer entered sloppily is the same item — two check-ins, one row in
    # `item`. This is what makes rating noise measurable at all (docs/10).
    again = db.find_or_create_item(con, " blonde ", maker="alexander")
    assert again == first
    db.add_checkin(con, again, rating=5, answers=[], tags=["home"],
                   at=datetime.fromisoformat("2026-09-05T20:00"))
    assert con.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM checkin").fetchone()[0] == 2
    assert [r["id"] for r in db.recent_items(con)] == [first]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nall checks passed")
