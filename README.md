# Bible Knowledge Anki Decks

A source-controlled collection of Bible-knowledge flashcards, built into **one canonical Anki package**.

## Install

Import this URL into AnkiMobile or Anki Desktop:

`https://raw.githubusercontent.com/cryppadotta/decks/main/dist/bible-knowledge.apkg`

The filename and URL stay the same as the repository grows. Re-importing an updated `.apkg` lets Anki add new notes and update previously imported notes while preserving scheduling/review history, provided the note type remains compatible.

## Current deck hierarchy

```text
Bible Knowledge
├── Old Testament
│   └── Book Summaries
└── New Testament
    └── Book Summaries
```

## Source catalog

| Module | Cards | Source |
| --- | ---: | --- |
| [Old Testament Book Summaries](decks/old-testament-book-summaries/) | 39 | [`cards.tsv`](decks/old-testament-book-summaries/cards.tsv) |
| [New Testament Book Summaries](decks/new-testament-book-summaries/) | 27 | [`cards.tsv`](decks/new-testament-book-summaries/cards.tsv) |

Total: **66 cards**.

## Repository layout

```text
build.py                     # canonical package builder using Anki's own backend
requirements.txt             # pinned Anki version
Makefile
.github/workflows/build.yml  # builds, validates, and commits the package

decks/
  <module>/
    README.md
    cards.tsv                # canonical editable source

dist/
  bible-knowledge.apkg       # the one supported install artifact
```

## Building locally

The package is generated with Anki's official Python backend, pinned in `requirements.txt`.

```bash
make setup
make build
```

`build.py` validates that:

- all expected cards were loaded,
- Anki produced the modern package format (`meta` + `collection.anki21b`),
- the package imports successfully into a clean Anki collection,
- importing the exact package a second time is idempotent and does not duplicate notes.

## Adding a new module

1. Add a directory under `decks/` with a `cards.tsv` source file.
2. Add that source and desired Anki deck path to `SOURCES` in `build.py`.
3. Update this catalog.
4. Push to `main`.

GitHub Actions rebuilds and replaces `dist/bible-knowledge.apkg`, so the public installation URL does not change.
