.PHONY: setup build verify

setup:
	python3 -m pip install -r requirements.txt

build:
	python3 build.py

verify:
	python3 build.py --verify-only
