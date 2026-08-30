# New Testament Book Summaries

Twenty-seven basic Anki cards: one card for each New Testament book.

The front is the book name; the back is a one-sentence summary intended to capture the book's main argument or purpose rather than merely list its contents. The summaries are written from a broadly Reformed evangelical perspective.

## Files

- `cards.tsv` — canonical source; columns are `Front`, `Back`, and `Tags`.
- `build.py` — dependency-free builder for the Anki package.
- `dist/new-testament-book-summaries.apkg` — generated package for installation.

## Deck name

`Bible Knowledge::New Testament::Book Summaries`

## Tags

- `NT::Gospels`
- `NT::History`
- `NT::Pauline_Epistles`
- `NT::General_Epistles`
- `NT::Prophecy`

## Build

From the repository root:

```bash
python3 decks/new-testament-book-summaries/build.py
```

The output is written to `decks/new-testament-book-summaries/dist/new-testament-book-summaries.apkg`.
