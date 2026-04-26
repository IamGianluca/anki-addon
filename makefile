.PHONY: install jupyter test test_slow static_check format clean test_update_baseline test_slow_update_baseline

install:
	uv sync --all-extras && \
	uv pip install -e . 

jupyter:
	uv run jupyter lab --ip 0.0.0.0 --no-browser --allow-root --port 8888

test:
	@START=$$(date +%s%N); \
	uv run pytest tests/unit/ -m "not slow"; \
	EXIT=$$?; \
	END=$$(date +%s%N); \
	ELAPSED=$$(( (END - START) )); \
	python3 scripts/gate_test_time.py --elapsed $$ELAPSED --suite test; \
	exit $$EXIT

test_update_baseline:
	@START=$$(date +%s%N); \
	uv run pytest tests/unit/ -m "not slow"; \
	EXIT=$$?; \
	END=$$(date +%s%N); \
	ELAPSED=$$(( (END - START) )); \
	python3 scripts/gate_test_time.py --elapsed $$ELAPSED --suite test --update-baseline; \
	exit $$EXIT

test_with_coverage:
	uv run pytest . -m "not slow" --ignore=tests/integration/ --ignore=tests/e2e/ --durations=5 --cov=src/addon/ --cov-report term-missing -vv

test_slow:
	@START=$$(date +%s%N); \
	uv run pytest . --durations=5 --cov=src/addon/ --cov-report term-missing -vv; \
	EXIT=$$?; \
	END=$$(date +%s%N); \
	ELAPSED=$$(( (END - START) )); \
	python3 scripts/gate_test_time.py --elapsed $$ELAPSED --suite test_slow; \
	exit $$EXIT

test_slow_update_baseline:
	@START=$$(date +%s%N); \
	uv run pytest . --durations=5 --cov=src/addon/ --cov-report term-missing -vv; \
	EXIT=$$?; \
	END=$$(date +%s%N); \
	ELAPSED=$$(( (END - START) )); \
	python3 scripts/gate_test_time.py --elapsed $$ELAPSED --suite test_slow --update-baseline; \
	exit $$EXIT

format:
	uv run ruff check --fix && uv run ruff format

static_check:
	# uvx (instead of uv run) ensures we always use the latest ty, keeping in sync with CI
	uvx ty@latest check ./src/

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
