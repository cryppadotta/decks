.PHONY: build nt-book-summaries

build: nt-book-summaries

nt-book-summaries:
	python3 decks/new-testament-book-summaries/build.py
