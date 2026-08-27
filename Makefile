.PHONY: help install sync migrate makemigrations run test test-fast coverage lint format \
        celery flower stripe-webhook seed superuser docker-build deps-lock check check-deploy \
        translations

PROJECT_DIR := myshop
TEST_ENV := DJANGO_SETTINGS_MODULE=myshop.settings.testing

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?##"}{printf "  %-18s %s\n", $$1, $$2}'

install: ## Sync venv from pyproject (uv) + copy .env
	cd $(PROJECT_DIR) && uv sync
	@test -f .env || cp -n .env.example .env || true

sync: ## Re-sync deps from pyproject
	cd $(PROJECT_DIR) && uv sync

migrate: ## Apply DB migrations
	cd $(PROJECT_DIR) && uv run python manage.py migrate

makemigrations: ## Generate new migrations
	cd $(PROJECT_DIR) && uv run python manage.py makemigrations

run: ## Run dev server on :8000
	cd $(PROJECT_DIR) && uv run python manage.py runserver

test: ## Run full test suite under testing settings
	cd $(PROJECT_DIR) && $(TEST_ENV) uv run python manage.py test

test-fast: ## Run tests with --keepdb for faster reruns
	cd $(PROJECT_DIR) && $(TEST_ENV) uv run python manage.py test --keepdb

coverage: ## Run tests with coverage report
	cd $(PROJECT_DIR) && $(TEST_ENV) uv run coverage run manage.py test
	cd $(PROJECT_DIR) && uv run coverage report

lint: ## Ruff lint check
	cd $(PROJECT_DIR) && uv run ruff check

format: ## Ruff format + auto-fix
	cd $(PROJECT_DIR) && uv run ruff check --fix
	cd $(PROJECT_DIR) && uv run ruff format

check: ## Django system check
	cd $(PROJECT_DIR) && uv run python manage.py check

check-deploy: ## Django deploy check against production settings
	cd $(PROJECT_DIR) && DJANGO_SETTINGS_MODULE=myshop.settings.production uv run python manage.py check --deploy

translations: ## Extract + DeepL-translate + compile message catalogs (run after adding {% trans %})
	sh scripts/update-translations.sh

celery: ## Start Celery worker
	cd $(PROJECT_DIR) && uv run celery -A myshop worker -l info

flower: ## Start Flower (basic-auth admin:admin)
	cd $(PROJECT_DIR) && uv run celery -A myshop flower --basic-auth=admin:admin

stripe-webhook: ## Forward Stripe webhooks to local dev server
	./stripe listen --forward-to 127.0.0.1:8000/payment/webhook/

seed: ## Load demo data (categories + products + posts)
	cd $(PROJECT_DIR) && uv run python manage.py seed_demo

superuser: ## Create Django superuser
	cd $(PROJECT_DIR) && uv run python manage.py createsuperuser

deps-lock: ## Regenerate requirements.txt for Docker from pyproject.toml
	uv pip compile $(PROJECT_DIR)/pyproject.toml -o requirements.txt --python-platform linux

docker-build: ## Build production Docker image
	docker build -t myshop .
