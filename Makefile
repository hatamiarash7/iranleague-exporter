.PHONY: shell install lock run lint format typecheck test test-cov clean vuln help
.DEFAULT_GOAL := help

shell: ## Activate virtual environment
	@poetry shell

install: ## Install dependencies
	@poetry install --with=dev,test

lock: ## Update poetry.lock
	@poetry lock

run: ## Run project
	@AUTH_USERNAME=admin AUTH_PASSWORD=1234 LOG_LEVEL=DEBUG poetry run start

test: ## Run tests
	@poetry run pytest -v

test-cov: ## Run tests with coverage
	@poetry run pytest --cov-report html:htmlcov --cov-report term --cov=iranleague_exporter

lint: ## Lint code with ruff and pylint
	@poetry run ruff check iranleague_exporter tests
	@poetry run pylint iranleague_exporter

format: ## Format code with ruff
	@poetry run ruff format iranleague_exporter tests
	@poetry run ruff check --fix iranleague_exporter tests

typecheck: ## Run type checking with mypy
	@poetry run mypy iranleague_exporter

clean: ## Clean up generated files
	@rm -rf htmlcov .coverage .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

vuln: ## Check for vulnerabilities
	osv-scanner scan --lockfile poetry.lock
	bandit -r . --severity-level=high --exclude ./.venv,./.git

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

