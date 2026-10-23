.DEFAULT_GOAL := help
.PHONY: help install run dev test check dod migrate clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run the app
	uvicorn app.main:app --host 0.0.0.0 --port 8080

dev: ## Run with auto-reload
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

test: ## Run all tests
	python -m pytest tests/ -v

check: ## Full quality gate
	ruff check . && ruff format --check . && python -m pytest tests/ -q --cov=app --cov-fail-under=85

dod: ## Run Definition of Done
	bash scripts/dod_check.sh

migrate: ## Apply migrations
	alembic upgrade head

clean: ## Remove caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f raqib.db
