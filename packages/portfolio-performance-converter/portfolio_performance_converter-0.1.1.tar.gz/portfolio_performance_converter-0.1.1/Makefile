.PHONY: check lint type-check test install clean build publish

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .

type-check:
	uv run mypy src

test:
	uv run pytest

check: lint type-check test

clean:
	rm -rf dist build *.egg-info

build: clean
	uv build

publish: build
	uv publish
