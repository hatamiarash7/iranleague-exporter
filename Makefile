.PHONY: shell install lock run lint help
.DEFAULT_GOAL := help

shell: ## Activate virtual environment
	@poetry shell

install: ## Install dependencies
	@poetry install --with=dev

lock: ## Update poetry.lock
	@poetry lock

run: ## Run project
	@AUTH_USERNAME=admin AUTH_PASSWORD=1234 LOG_LEVEL=DEBUG poetry run start

test: ## Run tests
	@poetry run pytest --cov-report html:htmlcov --cov-report term --cov=iranleague_exporter

lint: ## Lint code
	@poetry run pylint iranleague_exporter

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

