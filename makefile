.PHONY: install test test_slow check format lint clean 

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

clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".coverage.*" -delete
	@echo "Done!"
