DB_USER := emol_db_user
DB_PASSWORD := emol_db_password
DB_ROOT_PASSWORD := root_password
DB_NAME := emol
APP_WORKDIR := /opt/emol

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

ensure-up: ## Ensure containers are running (wait for health)
	@docker compose up -d --wait

cycle-all: down build up logs

down-app:
	docker compose down app

build-app:
	docker compose build app

cycle-app: down-app build-app up logs

# =============================================================================
# Development
# =============================================================================

shell: ## Open bash shell in app container
	docker compose exec app /bin/bash

manage: ## Run Django management command (interactive)
	@read -p "Command: " cmd && \
	docker compose exec app poetry run python manage.py $$cmd

migrate: ## Run Django migrations
	docker compose exec app poetry run python manage.py migrate

collectstatic: ## Collect static files
	docker compose exec app poetry run python manage.py collectstatic --noinput

# =============================================================================
# Database
# =============================================================================

db: ## Connect to MySQL database
	docker compose exec db mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME)

db-root: ## Connect to MySQL as root
	docker compose exec db mysql -u root -p$(DB_ROOT_PASSWORD)

db-dump: ## Dump database to file
	@echo "Dumping to emol_dump_$$(date +%Y%m%d_%H%M%S).sql"
	docker compose exec -T db mysqldump -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) > \
		emol_dump_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from dump file
	@read -p "Dump file: " f && \
	docker compose exec -T db mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) < $$f

# =============================================================================
# Code Quality (runs in Docker)
# =============================================================================

format: ensure-up
	docker compose exec -w $(APP_WORKDIR) app poetry run black .
	docker compose exec -w $(APP_WORKDIR) app poetry run isort .

lint: ensure-up
	docker compose exec -w $(APP_WORKDIR) app poetry run flake8 .

pylint: ensure-up
	docker compose exec -w $(APP_WORKDIR) app poetry run pylint --recursive=yes .

types: ensure-up
	docker compose exec -w $(APP_WORKDIR) app poetry run mypy .

check: ensure-up
	docker compose exec -w $(APP_WORKDIR) app poetry run black .
	docker compose exec -w $(APP_WORKDIR) app poetry run isort .
	docker compose exec -w $(APP_WORKDIR) app poetry run flake8 .
	docker compose exec -w $(APP_WORKDIR) app poetry run pylint --recursive=yes .
	docker compose exec -w $(APP_WORKDIR) app poetry run mypy .

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests in container
	@docker compose up -d --wait
	docker compose exec app poetry run python manage.py test

rebuild-test: ## Rebuild app container and run tests
	docker compose stop app
	docker compose build app
	docker compose up -d app --wait
	docker compose exec app poetry run python manage.py test

# =============================================================================
# Environment Setup
# =============================================================================

bootstrap: ## First-time setup: build containers and initialize ev
