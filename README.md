# Anki Decks

A source-controlled collection of Anki decks.

Each deck lives under `decks/<deck-name>/` and contains its canonical source data, a reproducible build script, deck-specific documentation, and a committed `.apkg` under `dist/` for direct installation on AnkiMobile or Anki Desktop.

## Deck catalog

| Deck | Description | Source | Download |
| --- | --- | --- | --- |
| [New Testament Book Summaries](decks/new-testament-book-summaries/) | One-sentence summaries of all 27 New Testament books, written from a broadly Reformed evangelical perspective. | [`cards.tsv`](decks/new-testament-book-summaries/cards.tsv) | [`new-testament-book-summaries.apkg`](decks/new-testament-book-summaries/dist/new-testament-book-summaries.apkg) |
| [Old Testament Book Summaries](decks/old-testament-book-summaries/) | One-sentence summaries of all 39 books of the Protestant Old Testament canon, written from a broadly Reformed evangelical perspective. | [`cards.tsv`](decks/old-testament-book-summaries/cards.tsv) | [`old-testament-book-summaries.apkg`](decks/old-testament-book-summaries/dist/old-testament-book-summaries.apkg) |

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

Build every deck:

```bash
make build
```

Or build a single deck:

```bash
make nt-book-summaries
make ot-book-summaries
```

You can also run a deck's builder directly, for example:

```bash
python3 decks/old-testament-book-summaries/build.py
```

The build scripts use only the Python standard library so the repository does not require Anki or third-party Python packages to produce the `.apkg` files.
