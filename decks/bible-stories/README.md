# Bible Stories

A location-memory deck for major biblical narratives, miracles, encounters, and parables.

The front names the story or event; the back gives the book and chapter(s) where it appears. When a Gospel story has parallel accounts, the card includes the major parallel references rather than choosing only one Gospel.

This deck intentionally focuses on *where stories are found*, not on extracting doctrines or theological propositions from them. Those can live in separate decks later.

## Anki deck path

`Bible Knowledge::Bible Stories`

## Source

- `cards.tsv` — canonical editable source

## Tags

Stories are tagged hierarchically, for example:

- `BibleStories::OT::Genesis`
- `BibleStories::OT::1Samuel`
- `BibleStories::NT::Gospels`
- `BibleStories::NT::Parables`
- `BibleStories::NT::Acts`

## Build

The repository has one canonical package. From the repository root:

```bash
make build
```

The output is:

`dist/bible-knowledge.apkg`
