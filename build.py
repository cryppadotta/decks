#!/usr/bin/env python3
"""Build the canonical Bible Knowledge Anki package with Anki's own exporter."""

from __future__ import annotations

import argparse
import csv
import hashlib
import tempfile
import zipfile
from pathlib import Path

from anki.collection import (
    Collection,
    DeckIdLimit,
    ExportAnkiPackageOptions,
    ImportAnkiPackageOptions,
    ImportAnkiPackageRequest,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dist" / "bible-knowledge.apkg"
ROOT_DECK = "Bible Knowledge"
NOTETYPE_NAME = "Bible Knowledge Basic"

SOURCES = [
    (
        ROOT / "decks" / "old-testament-book-summaries" / "cards.tsv",
        "Bible Knowledge::Old Testament::Book Summaries",
        "book-summary:ot",
    ),
    (
        ROOT / "decks" / "new-testament-book-summaries" / "cards.tsv",
        "Bible Knowledge::New Testament::Book Summaries",
        "book-summary:nt",
    ),
    (
        ROOT / "decks" / "bible-stories" / "cards.tsv",
        "Bible Knowledge::Bible Stories",
        "bible-story",
    ),
]

BASE91 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*+,-./:;<=>?@[]^_`{|}~"


def stable_guid(namespace: str, key: str) -> str:
    """Return an Anki-compatible deterministic GUID from a stable logical key."""
    value = int.from_bytes(
        hashlib.sha256(f"{namespace}\0{key}".encode("utf-8")).digest()[:8], "big"
    )
    chars: list[str] = []
    while value:
        value, idx = divmod(value, len(BASE91))
        chars.append(BASE91[idx])
    return "".join(reversed(chars)) or "a"


def read_source(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        raise RuntimeError(f"No cards in {path}")
    if set(rows[0]) != {"Front", "Back", "Tags"}:
        raise RuntimeError(f"Unexpected columns in {path}: {list(rows[0])}")
    return rows


def source_count() -> int:
    return sum(len(read_source(path)) for path, _, _ in SOURCES)


def create_notetype(col: Collection):
    notetype = col.models.new(NOTETYPE_NAME)
    col.models.add_field(notetype, col.models.new_field("Front"))
    col.models.add_field(notetype, col.models.new_field("Back"))
    template = col.models.new_template("Card 1")
    template["qfmt"] = "{{Front}}"
    template["afmt"] = '{{FrontSide}}<hr id="answer">{{Back}}'
    col.models.add_template(notetype, template)
    notetype["css"] = """.card {
  font-family: -apple-system, BlinkMacSystemFont, \"Helvetica Neue\", Arial, sans-serif;
  font-size: 24px;
  text-align: left;
  line-height: 1.45;
  color: black;
  background-color: white;
  padding: 18px;
}
"""
    col.models.add(notetype)
    return notetype


def populate_collection(path: Path) -> tuple[Collection, int]:
    col = Collection(str(path))
    notetype = create_notetype(col)
    root_id = col.decks.id(ROOT_DECK, create=True)
    assert root_id is not None

    seen_guids: set[str] = set()
    expected = source_count()
    total = 0
    for source_path, deck_name, namespace in SOURCES:
        deck_id = col.decks.id(deck_name, create=True)
        assert deck_id is not None
        for row in read_source(source_path):
            front = row["Front"].strip()
            back = row["Back"].strip()
            tag = row["Tags"].strip()
            guid = stable_guid(namespace, front)
            if guid in seen_guids:
                raise RuntimeError(f"Duplicate GUID generated for {namespace}:{front}")
            seen_guids.add(guid)

            note = col.new_note(notetype)
            note.guid = guid
            note["Front"] = front
            note["Back"] = back
            if tag:
                note.tags = [tag]
            col.add_note(note, deck_id)
            total += 1

    if total != expected or col.note_count() != expected or col.card_count() != expected:
        raise RuntimeError(
            f"Expected {expected} notes/cards; got source={total}, "
            f"notes={col.note_count()}, cards={col.card_count()}"
        )
    return col, expected


def export_package(output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        col, expected = populate_collection(Path(tmp) / "source.anki2")
        root_id = col.decks.id_for_name(ROOT_DECK)
        assert root_id is not None
        count = col.export_anki_package(
            out_path=str(output),
            options=ExportAnkiPackageOptions(
                with_scheduling=False,
                with_deck_configs=False,
                with_media=False,
                legacy=False,
            ),
            limit=DeckIdLimit(root_id),
        )
        col.close()

    if count != expected:
        raise RuntimeError(f"Anki exported {count} cards; expected {expected}")
    return expected


def import_request(package: Path) -> ImportAnkiPackageRequest:
    return ImportAnkiPackageRequest(
        package_path=str(package),
        options=ImportAnkiPackageOptions(
            merge_notetypes=True,
            update_notes=1,
            update_notetypes=1,
            with_scheduling=False,
            with_deck_configs=False,
        ),
    )


def verify_package(package: Path, expected: int | None = None) -> None:
    if expected is None:
        expected = source_count()
    if not package.exists():
        raise RuntimeError(f"Missing package: {package}")

    with zipfile.ZipFile(package) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"Corrupt ZIP member: {bad_member}")
        members = set(archive.namelist())
        required = {"meta", "collection.anki21b", "media"}
        if not required.issubset(members):
            raise RuntimeError(
                f"Expected modern Anki package members {sorted(required)}; got {sorted(members)}"
            )

    expected_decks = [deck_name for _, deck_name, _ in SOURCES]
    with tempfile.TemporaryDirectory() as tmp:
        col = Collection(str(Path(tmp) / "verify.anki2"))
        col.import_anki_package(import_request(package))
        if col.note_count() != expected or col.card_count() != expected:
            raise RuntimeError(
                f"First import produced {col.note_count()} notes / {col.card_count()} cards; expected {expected}"
            )
        for deck_name in expected_decks:
            if col.decks.id_for_name(deck_name) is None:
                raise RuntimeError(f"Missing imported deck: {deck_name}")

        col.import_anki_package(import_request(package))
        if col.note_count() != expected or col.card_count() != expected:
            raise RuntimeError(
                "Re-import was not idempotent: "
                f"{col.note_count()} notes / {col.card_count()} cards"
            )
        col.close()

    print(
        f"Verified {package}: {expected} cards across {len(SOURCES)} source decks, "
        "modern package format, clean import and idempotent re-import."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    output = args.output.resolve()
    if args.verify_only:
        verify_package(output)
    else:
        expected = export_package(output)
        verify_package(output, expected)


if __name__ == "__main__":
    main()
