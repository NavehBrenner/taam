"""SQLite store for items and check-ins.

Schema per `docs/04-data-model.md`, minus the tables nothing writes yet.
`profile` and `palate` arrive with M0/M3; adding a table to SQLite later is
cheap, carrying an empty one around is not.

    from taam.storage import db
    con = db.connect()            # data/taam.db, or $TAAM_DB

The file is gitignored and the pre-commit hook refuses to stage it — it is
personal data in a public repo (ADR-0001).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime

DEFAULT_PATH = pathlib.Path(__file__).resolve().parents[3] / "data" / "taam.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS item (
    id              INTEGER PRIMARY KEY,
    domain          TEXT NOT NULL DEFAULT 'beer',
    name            TEXT NOT NULL,
    maker           TEXT,
    identity_key    TEXT NOT NULL UNIQUE,
    style           TEXT,
    abv             REAL,
    ibu             REAL,
    srm             REAL,
    description     TEXT,
    community_score REAL,
    community_n     INTEGER,
    source          TEXT NOT NULL DEFAULT 'manual',
    source_id       TEXT,
    retrieved_at    TEXT
);

CREATE TABLE IF NOT EXISTS checkin (
    id        INTEGER PRIMARY KEY,
    item_id   INTEGER NOT NULL REFERENCES item(id),
    at        TEXT NOT NULL,          -- when drunk
    logged_at TEXT NOT NULL,          -- when typed, so backfill is visible as such
    rating    REAL,
    notes     TEXT
);

CREATE TABLE IF NOT EXISTS checkin_answer (
    checkin_id       INTEGER NOT NULL REFERENCES checkin(id),
    question_id      TEXT NOT NULL,
    question_version INTEGER NOT NULL,   -- a reworded question is not the same question
    answer           TEXT NOT NULL       -- json
);

CREATE TABLE IF NOT EXISTS checkin_context (
    checkin_id    INTEGER PRIMARY KEY REFERENCES checkin(id),
    tags          TEXT NOT NULL,        -- json array
    time_of_day   TEXT,
    temperature_c REAL,
    intent        TEXT
);

CREATE INDEX IF NOT EXISTS checkin_at ON checkin(at DESC);
"""


def connect(path: str | pathlib.Path | None = None) -> sqlite3.Connection:
    """Open the store, creating it if needed."""
    path = pathlib.Path(path or os.environ.get("TAAM_DB") or DEFAULT_PATH)
    if path != pathlib.Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def identity_key(name: str, maker: str | None) -> str:
    """Normalised dedup key: lowercased, alphanumerics only, maker first.

    ponytail: D-015 is still open (NVB-90). This is the crudest key that stops
    the same beer being entered twice, and it is recomputable from name+maker
    with one UPDATE, so it locks nothing. Upgrade when a catalog is populated
    and real collisions show up.
    """
    slug = re.sub(r"[^a-z0-9]+", "", f"{maker or ''}{name}".lower())
    return slug or (maker or "") + name


def time_of_day(when: datetime) -> str:
    """Coarse bucket. Cheap context that costs one tap: none."""
    h = when.hour
    if h < 6:
        return "night"
    if h < 11:
        return "morning"
    if h < 15:
        return "noon"
    if h < 18:
        return "afternoon"
    return "evening"


def find_or_create_item(con: sqlite3.Connection, name: str, **fields: object) -> int:
    """Return the item id, inserting it if this is the first sighting."""
    maker = fields.get("maker")
    key = identity_key(name, maker if isinstance(maker, str) else None)
    row = con.execute("SELECT id FROM item WHERE identity_key = ?", (key,)).fetchone()
    if row:
        return int(row["id"])
    cols = ["name", "identity_key", *fields]
    vals = [name, key, *fields.values()]
    cur = con.execute(
        f"INSERT INTO item ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals)
    return int(cur.lastrowid or 0)


def recent_items(con: sqlite3.Connection, limit: int = 8) -> list[sqlite3.Row]:
    """Most recently drunk items, newest first. You often drink what you drank."""
    return con.execute(
        """SELECT i.id, i.name, i.maker, MAX(c.at) AS last_at
           FROM item i JOIN checkin c ON c.item_id = i.id
           GROUP BY i.id ORDER BY last_at DESC LIMIT ?""", (limit,)).fetchall()


def search_items(con: sqlite3.Connection, text: str, limit: int = 8) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT id, name, maker FROM item
           WHERE name LIKE ? OR maker LIKE ? ORDER BY name LIMIT ?""",
        (f"%{text}%", f"%{text}%", limit)).fetchall()


def last_tags(con: sqlite3.Connection) -> list[str]:
    """Tags from the most recent check-in, to pre-fill the next one."""
    row = con.execute(
        """SELECT x.tags FROM checkin_context x JOIN checkin c ON c.id = x.checkin_id
           ORDER BY c.at DESC LIMIT 1""").fetchone()
    return json.loads(row["tags"]) if row else []


def add_checkin(
    con: sqlite3.Connection,
    item_id: int,
    rating: float | None,
    answers: Sequence[tuple[str, int, object]],
    tags: list[str],
    notes: str | None = None,
    at: datetime | None = None,
    intent: str | None = None,
) -> int:
    """Write one check-in and its answers and context, atomically."""
    at = (at or datetime.now(UTC)).astimezone()  # local offset: where it was drunk matters
    with con:
        cur = con.execute(
            "INSERT INTO checkin (item_id, at, logged_at, rating, notes) VALUES (?,?,?,?,?)",
            (item_id, at.isoformat(timespec="seconds"),
             datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
             rating, notes or None))
        checkin_id = int(cur.lastrowid or 0)
        con.executemany(
            "INSERT INTO checkin_answer VALUES (?,?,?,?)",
            [(checkin_id, qid, ver, json.dumps(ans)) for qid, ver, ans in answers])
        con.execute(
            "INSERT INTO checkin_context (checkin_id, tags, time_of_day, intent) VALUES (?,?,?,?)",
            (checkin_id, json.dumps(tags), time_of_day(at), intent))
    return checkin_id
