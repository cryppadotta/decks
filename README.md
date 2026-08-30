# Anki Decks

A source-controlled collection of Anki decks.

Each deck lives under `decks/<deck-name>/` and contains its canonical source data, a reproducible build script, deck-specific documentation, and a committed `.apkg` under `dist/` for direct installation on AnkiMobile or Anki Desktop.

## Deck catalog

| Deck | Description | Source | Download |
| --- | --- | --- | --- |
| [New Testament Book Summaries](decks/new-testament-book-summaries/) | One-sentence summaries of all 27 New Testament books, written from a broadly Reformed evangelical perspective. | [`cards.tsv`](decks/new-testament-book-summaries/cards.tsv) | [`new-testament-book-summaries.apkg`](decks/new-testament-book-summaries/dist/new-testament-book-summaries.apkg) |

## Repository layout

```text
decks/
  <deck-name>/
    README.md       # scope, conventions, and deck metadata
    cards.tsv       # canonical editable source
    build.py        # dependency-free package builder
    dist/
      <deck>.apkg   # generated installable artifact
```

## Building

Build an individual deck from the repository root:

```bash
python3 decks/new-testament-book-summaries/build.py
```

Or use:

```bash
make build
```

The build scripts use only the Python standard library so the repository does not require Anki or third-party Python packages to produce the `.apkg` files.
