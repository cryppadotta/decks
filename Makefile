.PHONY: build nt-book-summaries ot-book-summaries

build: nt-book-summaries ot-book-summaries

nt-book-summaries:
	python3 decks/new-testament-book-summaries/build.py

ot-book-summaries:
	python3 decks/old-testament-book-summaries/build.py
