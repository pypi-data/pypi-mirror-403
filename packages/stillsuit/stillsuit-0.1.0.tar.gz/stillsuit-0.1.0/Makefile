.PHONY: all test lint format docs

all: format lint test

test:
	PYTHONPATH=src pytest -v .

lint:
	flake8 .

format:
	isort .
	black .

docs:
	mkdocs build
