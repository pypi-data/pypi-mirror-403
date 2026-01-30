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

docker-build:
	docker build -t ghcr.io/marmol-dev/portfolio-performance-converter:latest .

docker-build-multi:
	docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/marmol-dev/portfolio-performance-converter:latest .

docker-run-web:
	docker run --rm -p 7860:7860 ghcr.io/marmol-dev/portfolio-performance-converter:latest web

docker-run-cli:
	docker run --rm -v $(pwd)/data:/data ghcr.io/marmol-dev/portfolio-performance-converter:latest -h
