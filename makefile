install:
	uv sync --all-extras && \
	uv pip install -e . 

test:
	pytest . -vv

test_slow:
	pytest . --durations=5 --cov=src/anki_ai/ --cov-report term-missing -vv

check: format lint

format:
	ruff check --select I --fix
	ruff format

lint:
	ruff check --fix
