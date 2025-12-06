# Variables
APP_CONTAINER := emol-app-1
DB_CONTAINER := emol-db-1
DB_USER := emol_db_user
DB_PASSWORD := emol_db_password
DB_ROOT_PASSWORD := root_password
DB_NAME := emol

.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' Makefile | sort | \
		awk -F ':.*?## ' '{printf "%-20s %s\n", $$1, $$2}'

# =============================================================================
# Docker Compose Operations
# =============================================================================

build: ## Build containers
	docker compose build

up: ## Start containers in background
	docker compose up -d

down: ## Stop containers
	docker compose down

logs: ## Tail app container logs
	docker compose logs -f app

status: ## Show container status
	docker compose ps

prune: ## Remove unused Docker images
	docker image prune -f

full-cycle: down build up logs

# =============================================================================
# Development
# =============================================================================

shell: ## Open bash shell in app container
	docker exec -it $(APP_CONTAINER) /bin/bash

manage: ## Run Django management command (interactive)
	@read -p "Command: " cmd && \
	docker exec -it $(APP_CONTAINER) poetry run python manage.py $$cmd

migrate: ## Run Django migrations
	docker exec -it $(APP_CONTAINER) poetry run python manage.py migrate

collectstatic: ## Collect static files
	docker exec -it $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput

# =============================================================================
# Database
# =============================================================================

db: ## Connect to MySQL database
	docker exec -it $(DB_CONTAINER) mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME)

db-root: ## Connect to MySQL as root
	docker exec -it $(DB_CONTAINER) mysql -u root -p$(DB_ROOT_PASSWORD)

db-dump: ## Dump database to file
	@echo "Dumping to emol_dump_$$(date +%Y%m%d_%H%M%S).sql"
	docker exec $(DB_CONTAINER) mysqldump -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) > \
		emol_dump_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from dump file
	@read -p "Dump file: " f && \
	docker exec -i $(DB_CONTAINER) mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) < $$f

# =============================================================================
# Code Quality (runs locally with Poetry)
# =============================================================================

install: ## Install dev dependencies locally
	poetry install --only dev

format: install ## Format code (black, isort)
	poetry run black emol/
	poetry run isort emol/

lint: install ## Lint code (flake8)
	poetry run flake8 emol/

pylint: install ## Run pylint
	poetry run pylint emol/

types: install ## Type check (mypy)
	poetry run mypy emol/

check: format lint types ## Run all code quality checks

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests in container
	@docker exec $(APP_CONTAINER) echo "OK" >/dev/null 2>&1 || (echo "Starting containers..." && docker compose up -d && sleep 10)
	docker exec -it $(APP_CONTAINER) poetry run python manage.py test

# =============================================================================
# Environment Setup
# =============================================================================

bootstrap: ## First-time setup: build containers and initialize everything
	@echo "🚀 Building development environment..."
	docker compose down -v
	docker compose build --no-cache
	docker compose up -d --wait
	@echo "🗄️  Running database setup..."
	docker exec -it $(APP_CONTAINER) poetry run python manage.py migrate
	docker exec -it $(APP_CONTAINER) poetry run python manage.py createcachetable
	docker exec -it $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput
	docker exec -it $(APP_CONTAINER) poetry run python manage.py ensure_superuser --non-interactive
	@echo ""
	@echo "✅ Bootstrap complete!"
	@echo "   http://localhost:8000"
	@echo ""
	@echo "   make up     - Start containers"
	@echo "   make down   - Stop containers"
	@echo "   make logs   - View logs"
	@echo "   make shell  - Container shell"

rebuild: ## Rebuild app container (preserves database)
	docker compose stop app
	docker compose build app
	docker compose up -d app --wait
	docker exec $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput
	docker exec $(APP_CONTAINER) poetry run python manage.py migrate
	@echo "✅ Rebuild complete"

setup: ## Quick setup for existing environment
	@docker exec $(APP_CONTAINER) echo "OK" >/dev/null 2>&1 || (docker compose up -d && sleep 10)
	docker exec $(APP_CONTAINER) poetry run python manage.py migrate
	docker exec $(APP_CONTAINER) poetry run python manage.py createcachetable 2>/dev/null || true
	docker exec $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput
	docker exec $(APP_CONTAINER) poetry run python manage.py ensure_superuser --non-interactive
	@echo "✅ Setup complete"

.PHONY: help build up down logs status prune shell manage migrate collectstatic \
        db db-root db-dump db-restore install format lint pylint types check test \
        bootstrap rebuild setup
