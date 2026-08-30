#!/usr/bin/env python3
"""Build the New Testament book-summary Anki package using only stdlib."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import tempfile
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "cards.tsv"
OUTPUT = HERE / "dist" / "new-testament-book-summaries.apkg"

DECK_ID = 2059400110
MODEL_ID = 1607392319
DECK_NAME = "Bible Knowledge::New Testament::Book Summaries"
MODEL_NAME = "Bible Book Summary"

BASE91_TABLE = list(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
)

SCHEMA = """
CREATE TABLE col (id integer primary key, crt integer not null, mod integer not null, scm integer not null,
ver integer not null, dty integer not null, usn integer not null, ls integer not null, conf text not null,
models text not null, decks text not null, dconf text not null, tags text not null);
CREATE TABLE notes (id integer primary key, guid text not null, mid integer not null, mod integer not null,
usn integer not null, tags text not null, flds text not null, sfld integer not null, csum integer not null,
flags integer not null, data text not null);
CREATE TABLE cards (id integer primary key, nid integer not null, did integer not null, ord integer not null,
mod integer not null, usn integer not null, type integer not null, queue integer not null, due integer not null,
ivl integer not null, factor integer not null, reps integer not null, lapses integer not null, left integer not null,
odue integer not null, odid integer not null, flags integer not null, data text not null);
CREATE TABLE revlog (id integer primary key, cid integer not null, usn integer not null, ease integer not null,
ivl integer not null, lastIvl integer not null, factor integer not null, time integer not null, type integer not null);
CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""


def guid_for(*values: str) -> str:
    digest = hashlib.sha256("__".join(values).encode("utf-8")).digest()[:8]
    value = int.from_bytes(digest, "big")
    chars: list[str] = []
    while value:
        chars.append(BASE91_TABLE[value % len(BASE91_TABLE)])
        value //= len(BASE91_TABLE)
    return "".join(reversed(chars))


def read_cards() -> list[dict[str, str]]:
    with SOURCE.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    expected = {"Front", "Back", "Tags"}
    if not rows or set(rows[0]) != expected:
        raise SystemExit(f"Expected TSV columns {sorted(expected)}")
    return rows


def build() -> None:
    cards = read_cards()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    timestamp = time.time()
    mod = int(timestamp)
    next_id = int(timestamp * 1000)

    def allocate_id() -> int:
        nonlocal next_id
        current = next_id
        next_id += 1
        return current

    conf = {
        "activeDecks": [1], "addToCur": True, "collapseTime": 1200,
        "curDeck": 1, "curModel": "1425279151691", "dueCounts": True,
        "estTimes": True, "newBury": True, "newSpread": 0, "nextPos": 1,
        "sortBackwards": False, "sortType": "noteFld", "timeLim": 0,
    }
    default_deck = {
        "collapsed": False, "conf": 1, "desc": "", "dyn": 0,
        "extendNew": 10, "extendRev": 50, "id": 1, "lrnToday": [0, 0],
        "mod": 1425279151, "name": "Default", "newToday": [0, 0],
        "revToday": [0, 0], "timeToday": [0, 0], "usn": 0,
    }
    deck = {
        "collapsed": False, "conf": 1,
        "desc": "One-sentence summaries of all 27 New Testament books.",
        "dyn": 0, "extendNew": 0, "extendRev": 50, "id": DECK_ID,
        "lrnToday": [0, 0], "mod": mod, "name": DECK_NAME,
        "newToday": [0, 0], "revToday": [0, 0], "timeToday": [0, 0], "usn": -1,
    }
    dconf = {
        "1": {
            "autoplay": True, "id": 1,
            "lapse": {"delays": [10], "leechAction": 0, "leechFails": 8, "minInt": 1, "mult": 0},
            "maxTaken": 60, "mod": 0, "name": "Default",
            "new": {"bury": True, "delays": [1, 10], "initialFactor": 2500,
                    "ints": [1, 4, 7], "order": 1, "perDay": 20, "separate": True},
            "replayq": True,
            "rev": {"bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1,
                    "maxIvl": 36500, "minSpace": 1, "perDay": 100},
            "timer": 0, "usn": 0,
        }
    }
    fields = [
        {"name": "Front", "ord": 0, "font": "Liberation Sans", "media": [], "rtl": False, "size": 20, "sticky": False},
        {"name": "Back", "ord": 1, "font": "Liberation Sans", "media": [], "rtl": False, "size": 20, "sticky": False},
    ]
    templates = [{
        "name": "Card 1", "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id=\"answer\">{{Back}}", "ord": 0,
        "bafmt": "", "bqfmt": "", "bfont": "", "bsize": 0, "did": None,
    }]
    model = {
        "css": ".card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }",
        "did": DECK_ID, "flds": fields, "id": str(MODEL_ID),
        "latexPost": "\\end{document}",
        "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n",
        "latexsvg": False, "mod": mod, "name": MODEL_NAME,
        "req": [[0, "all", [0]]], "sortf": 0, "tags": [], "tmpls": templates,
        "type": 0, "usn": -1, "vers": [],
    }

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "collection.anki2"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.executescript(SCHEMA)
        cur.execute(
            "INSERT INTO col VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (1, 1411124400, 1425279151694, 1425279151690, 11, 0, 0, 0,
             json.dumps(conf), json.dumps({str(MODEL_ID): model}),
             json.dumps({"1": default_deck, str(DECK_ID): deck}), json.dumps(dconf), "{}"),
        )

        for row in cards:
            note_id = allocate_id()
            front, back, tags = row["Front"], row["Back"], row["Tags"]
            cur.execute(
                "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (note_id, guid_for(front, back), MODEL_ID, mod, -1, f" {tags} ",
                 front + "\x1f" + back, front, 0, 0, ""),
            )
            cur.execute(
                "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (allocate_id(), note_id, DECK_ID, 0, mod, -1, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, ""),
            )

        conn.commit()
        integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        if integrity != "ok":
            raise SystemExit(f"SQLite integrity check failed: {integrity}")

        with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(db_path, "collection.anki2")
            archive.writestr("media", "{}")

    print(f"Built {OUTPUT} ({len(cards)} cards)")


if __name__ == "__main__":
    build()
