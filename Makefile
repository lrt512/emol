# Variables
APP_CONTAINER := emol-app-1
DB_CONTAINER := emol-db-1
DB_USER := emol_db_user
DB_PASSWORD := emol_db_password
DB_ROOT_PASSWORD := root_password
DB_NAME := emol

# Help and default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' Makefile | sort | \
		while read -r line; do \
			command=$$(echo "$$line" | cut -d':' -f1); \
			help_text=$$(echo "$$line" | cut -d'#' -f2- | sed -e 's/## //'); \
			printf "%-20s %s\n" "$$command" "$$help_text"; \
		done

# =============================================================================
# Docker Compose Operations
# =============================================================================

up: ## Start existing services (daily use - no rebuild)
	docker compose up

down: ## Stop all services
	docker compose down

up-detached: ## Start existing services in background (no rebuild)
	docker compose up -d

restart-app: ## Restart just the app container
	@echo "Cycling app container..."
	docker compose stop app
	docker compose rm -f app
	docker compose up -d --build app
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Checking container logs..."
	@docker compose logs --tail=50 app
	@echo "\nChecking service status..."
	@$(MAKE) status || true

prune: ## Remove unused Docker images
	docker image prune -f

# =============================================================================
# Development Environment
# =============================================================================

shell: ## Open bash shell in app container
	docker exec -it $(APP_CONTAINER) /bin/bash

manage: ## Run Django management command (interactive)
	@read -p "Enter management command: " command && \
	docker exec -it $(APP_CONTAINER) poetry run python manage.py $$command

migrate: ## Run Django migrations in container
	docker exec -it $(APP_CONTAINER) poetry run python manage.py migrate

logs: ## View app container logs (follow)
	docker compose logs -f app

nginx-logs: ## View nginx logs
	docker exec -it $(APP_CONTAINER) tail -f /var/log/nginx/error.log /var/log/nginx/access.log

app-logs: ## View application logs
	docker exec -it $(APP_CONTAINER) tail -f /var/log/emol/gunicorn.log

restart-services: ## Restart application services inside container
	@echo "Restarting application..."
	@docker exec $(APP_CONTAINER) bash -c '\
		echo "Stopping gunicorn..." && \
		/etc/init.d/emol stop && \
		echo "Starting gunicorn..." && \
		/etc/init.d/emol start && \
		echo "Application restarted"'

status: ## Check status of services inside container
	@echo "Checking nginx status..." && \
	docker exec -it $(APP_CONTAINER) service nginx status && \
	echo "\nChecking application status..." && \
	docker exec -it $(APP_CONTAINER) /etc/init.d/emol status

# =============================================================================
# Database Operations
# =============================================================================

db: ## Connect to MySQL database
	docker exec -it $(DB_CONTAINER) mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME)

db-root: ## Connect to MySQL as root
	docker exec -it $(DB_CONTAINER) mysql -u root -p$(DB_ROOT_PASSWORD)

db-dump: ## Dump the database to a file
	@echo "Dumping database to emol_dump_$$(date +%Y%m%d_%H%M%S).sql"
	docker exec $(DB_CONTAINER) mysqldump -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) > \
		emol_dump_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from a dump file
	@read -p "Enter dump file path: " dumpfile && \
	docker exec -i $(DB_CONTAINER) mysql -u $(DB_USER) -p$(DB_PASSWORD) $(DB_NAME) < $$dumpfile

# =============================================================================
# Code Quality and Testing
# =============================================================================

install: ## Install project dependencies with poetry
	poetry install

test: ## Run tests in container
	@if ! docker exec $(APP_CONTAINER) echo "Container is running" >/dev/null 2>&1; then \
		echo "Starting containers..."; \
		docker compose up -d --build; \
		echo "Waiting for services to start..."; \
		sleep 10; \
	fi
	@echo "Running tests..."
	@if ! docker exec -it $(APP_CONTAINER) poetry run python manage.py test; then \
		echo ""; \
		echo "❌ Tests failed. If you're getting import/module errors, try:"; \
		echo "   make bootstrap  # Complete environment setup"; \
		exit 1; \
	fi

check: check-format check-types check-lint check-test ## Run all checks (format, types, lint, test)

check-format: format ## Check code format (black, isort)
	@echo "Running format check..."
	poetry run black --check --diff .
	poetry run isort --check --diff .

check-types: types ## Check types with mypy
	@echo "Running type check..."
	poetry run mypy .

check-lint: lint ## Run linters (flake8)
	@echo "Running lint check..."
	poetry run flake8 .

check-test: test ## Run tests
	@echo "Running tests..."
	$(MAKE) test

lint: install ## Run flake8 linter
	poetry run flake8 .

pylint: install ## Run pylint linter (more strict)
	@touch __init__.py
	@poetry run pylint emol; status=$$?; rm -f __init__.py; exit $$status

types: install ## Run mypy type checker
	poetry run mypy .

format: install ## Format code with black and isort
	poetry run black .
	poetry run isort .

# =============================================================================
# Environment Setup
# =============================================================================

bootstrap: ## FIRST-TIME SETUP: Complete environment setup for new developers
	@echo "🚀 FIRST-TIME SETUP: Building and configuring development environment..."
	@echo "📦 Building containers from scratch..."
	docker compose down -v
	docker compose build --no-cache
	@echo "🔧 Starting services with health checks..."
	docker compose up -d --wait
	@echo "✅ All services are healthy and ready!"
	@echo "🗄️  Running database migrations..."
	docker exec -it $(APP_CONTAINER) poetry run python manage.py migrate
	@echo "📊 Creating cache table..."
	docker exec -it $(APP_CONTAINER) poetry run python manage.py createcachetable
	@echo "📁 Collecting static files..."
	docker exec -it $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput
	@echo "👤 Creating superuser..."
	docker exec -it $(APP_CONTAINER) poetry run python manage.py ensure_superuser --non-interactive
	@echo "🎯 Importing disciplines (if available)..."
	@docker exec -it $(APP_CONTAINER) poetry run python manage.py import_disciplines || echo "No disciplines to import or command not available"
	@echo ""
	@echo "🎉 Bootstrap complete! Your development environment is ready."
	@echo "📋 Daily development commands:"
	@echo "   make up          - Start services (daily use)"
	@echo "   make down        - Stop services"
	@echo "   make shell       - Open container shell"
	@echo "   make test        - Run tests"
	@echo "   make logs        - View application logs"
	@echo ""
	@echo "📋 Code changes are live-mounted (no rebuild needed!)"
	@echo "📋 Only use 'make rebuild' for dependency/structural changes"
	@echo ""
	@echo "🌐 Application available at: http://localhost:8000"

rebuild: ## Rebuild app container for structural changes (preserves database)
	@echo "🔄 Rebuilding app container for structural changes..."
	@echo "💾 Database and volumes will be preserved"
	@echo "ℹ️  Note: Code changes don't need rebuild (live-mounted)"
	docker compose stop app
	docker compose build app
	docker compose up -d app --wait
	@echo "✅ App container is healthy and ready!"
	@echo "📁 Collecting static files..."
	@docker exec $(APP_CONTAINER) poetry run python manage.py collectstatic --noinput || echo "Static collection skipped"
	@echo "🗄️  Running any new migrations..."
	@docker exec $(APP_CONTAINER) poetry run python manage.py migrate || echo "Migration skipped"
	@echo ""
	@echo "✅ Rebuild complete! Structural changes applied."
	@echo "💡 Remember: Code changes are live-mounted, rebuild only needed for:"
	@echo "   📦 Dependency changes (poetry.lock, requirements)"
	@echo "   🐳 Dockerfile changes"
	@echo "   ⚙️  System package changes"

setup: ## Quick setup for existing environment (production parity)
	@echo "⚡ Quick setup using production scripts..."
	$(MAKE) up-detached
	@echo "🔧 Running production bootstrap script in dev mode..."
	docker exec -it $(APP_CONTAINER) bash -c "cd /opt/emol && EMOL_DEV=1 ./setup_files/bootstrap.sh"
	@echo "✅ Setup complete!"

bootstrap-script: ## Run production bootstrap script manually (for debugging)
	@echo "🔧 Running production bootstrap script in dev mode..."
	docker exec -it $(APP_CONTAINER) bash -c "cd /opt/emol && EMOL_DEV=1 ./setup_files/bootstrap.sh"

# =============================================================================
# Deployment and Testing
# =============================================================================

bootstrap-test: ## Run bootstrap.sh and deploy.sh in a local Ubuntu container
	@echo "Running bootstrap.sh in a local Ubuntu container..."
	docker run --rm -it \
		-v $(CURDIR):/app \
		ubuntu:22.04 \
		/bin/bash -c "cd /app/setup_files && ./bootstrap.sh"
	@echo "Running deploy.sh in a local Ubuntu container..."
	docker run --rm -it \
		-v $(CURDIR):/app \
		ubuntu:22.04 \
		/bin/bash -c "cd /app/setup_files && ./deploy.sh"

# =============================================================================
# PHONY Declarations
# =============================================================================

.PHONY: help up down up-detached restart-app prune shell manage migrate logs \
        nginx-logs app-logs restart-services status db db-root db-dump db-restore \
        install test check check-format check-types check-lint check-test lint \
        pylint types format bootstrap rebuild setup bootstrap-script bootstrap-test 