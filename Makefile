.PHONY: help certs build up down logs test lint clean migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

certs: ## Generate self-signed SSL certificates
	@bash generate-certs.sh

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

test: ## Run tests
	docker-compose run --rm api pytest

test-cov: ## Run tests with coverage
	docker-compose run --rm api pytest --cov=app --cov-report=html

lint: ## Run linting with ruff
	docker-compose run --rm api ruff check .

format: ## Format code with ruff
	docker-compose run --rm api ruff format .

migrate: ## Run database migrations
	docker-compose run --rm api alembic upgrade head

migrate-create: ## Create a new migration (provide name with NAME=...)
	docker-compose run --rm api alembic revision --autogenerate -m "$(NAME)"

clean: ## Clean up containers, volumes, and images
	docker-compose down -v
	docker system prune -f

restart: down up ## Restart all services

shell-api: ## Open a shell in the API container
	docker-compose exec api sh

shell-db: ## Open a PostgreSQL shell
	docker-compose exec db psql -U livemenu -d livemenu

dev-setup: certs ## Setup development environment (generate certs and create .env)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "⚠️  Please update JWT_SECRET and IP_HASH_SALT in .env"; \
	else \
		echo "ℹ️  .env file already exists"; \
	fi
