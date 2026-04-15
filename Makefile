.PHONY: dev prod dev-down prod-down logs build clean db-migrate db-upgrade

DEV  = docker compose -f docker-compose.yml -f docker-compose.dev.yml
PROD = docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml

# --- Dev ---
dev: ## Start dev (hot reload, exposed ports)
	$(DEV) up -d --build

dev-down: ## Stop dev
	$(DEV) down

dev-logs: ## Tail dev logs
	$(DEV) logs -f $(s)

# --- Prod ---
prod: ## Start prod (tunnel, resource limits)
	$(PROD) up -d --build

prod-down: ## Stop prod
	$(PROD) down

prod-logs: ## Tail prod logs
	$(PROD) logs -f $(s)

# --- Shared ---
build: ## Build all images
	docker compose build

clean: ## Remove containers + volumes
	docker compose down -v --remove-orphans

# --- Database ---
db-migrate: ## Create migration (usage: make db-migrate m="add users table")
	$(DEV) exec backend alembic revision --autogenerate -m "$(m)"

db-upgrade: ## Apply migrations
	$(DEV) exec backend alembic upgrade head

db-upgrade-prod: ## Apply migrations (prod)
	$(PROD) exec backend alembic upgrade head

db-downgrade: ## Rollback one migration
	$(DEV) exec backend alembic downgrade -1

# --- Dev tools ---
shell: ## Shell into backend
	$(DEV) exec backend bash

lint: ## Run linters
	$(DEV) exec backend ruff check .

test: ## Run tests
	$(DEV) exec backend pytest -x -q

github-sync: ## Sync to public GitHub (excludes private files)
	./scripts/sync-github.sh

github-dry: ## Preview what would be excluded from GitHub
	./scripts/sync-github.sh --dry-run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
