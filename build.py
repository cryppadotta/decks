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
EXPECTED_NOTES = 66

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


def populate_collection(path: Path) -> Collection:
    col = Collection(str(path))
    notetype = create_notetype(col)

    # Creating the full names also creates the parent hierarchy.
    root_id = col.decks.id(ROOT_DECK, create=True)
    assert root_id is not None

    seen_guids: set[str] = set()
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

    if total != EXPECTED_NOTES:
        raise RuntimeError(f"Expected {EXPECTED_NOTES} source notes, found {total}")
    if col.note_count() != EXPECTED_NOTES or col.card_count() != EXPECTED_NOTES:
        raise RuntimeError(
            f"Collection has {col.note_count()} notes / {col.card_count()} cards; "
            f"expected {EXPECTED_NOTES}/{EXPECTED_NOTES}"
        )
    return col


def export_package(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        col_path = Path(tmp) / "source.anki2"
        col = populate_collection(col_path)
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

    if count != EXPECTED_NOTES:
        raise RuntimeError(f"Anki exported {count} cards; expected {EXPECTED_NOTES}")


def import_request(package: Path) -> ImportAnkiPackageRequest:
    return ImportAnkiPackageRequest(
        package_path=str(package),
        options=ImportAnkiPackageOptions(
            merge_notetypes=True,
            update_notes=1,      # ALWAYS
            update_notetypes=1,  # ALWAYS
            with_scheduling=False,
            with_deck_configs=False,
        ),
    )


def verify_package(package: Path) -> None:
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

    # Most important validation: ask the same Anki backend that produced the
    # package to import it into a clean collection. Then import it a second
    # time and ensure stable GUIDs make the operation idempotent.
    with tempfile.TemporaryDirectory() as tmp:
        col = Collection(str(Path(tmp) / "verify.anki2"))
        first = col.import_anki_package(import_request(package))
        if col.note_count() != EXPECTED_NOTES or col.card_count() != EXPECTED_NOTES:
            raise RuntimeError(
                f"First import produced {col.note_count()} notes / {col.card_count()} cards"
            )
        for deck_name in (
            "Bible Knowledge::Old Testament::Book Summaries",
            "Bible Knowledge::New Testament::Book Summaries",
        ):
            if col.decks.id_for_name(deck_name) is None:
                raise RuntimeError(f"Missing imported deck: {deck_name}")

        second = col.import_anki_package(import_request(package))
        if col.note_count() != EXPECTED_NOTES or col.card_count() != EXPECTED_NOTES:
            raise RuntimeError(
                "Re-import was not idempotent: "
                f"{col.note_count()} notes / {col.card_count()} cards"
            )
        col.close()

    print(
        f"Verified {package}: {EXPECTED_NOTES} cards, modern package format, "
        "clean import and idempotent re-import."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    output = args.output.resolve()
    if not args.verify_only:
        export_package(output)
    verify_package(output)


if __name__ == "__main__":
    main()
