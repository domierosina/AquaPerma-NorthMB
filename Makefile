
.PHONY: setup test lint quickstart

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

test:
	pytest

lint:
	flake8 src

quickstart:
	python -m src.cli --help
