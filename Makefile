.PHONY: help up down build logs api-logs frontend-logs db-shell api-shell test lint fmt clean sdk-install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────
up: ## Start all services (build if needed)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

build: ## Force rebuild all containers
	docker compose build --no-cache

logs: ## Tail all container logs
	docker compose logs -f

api-logs: ## Tail API logs
	docker compose logs -f api

frontend-logs: ## Tail frontend logs
	docker compose logs -f frontend

restart: ## Restart all services
	docker compose restart

# ── Development ───────────────────────────────────────────────────
dev-api: ## Run API locally with hot reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend dev server
	cd frontend && npm run dev

# ── Database ──────────────────────────────────────────────────────
db-shell: ## Open psql shell
	docker compose exec postgres psql -U cloudpulse -d cloudpulse

db-reset: ## Reset database (WARNING: destroys data)
	docker compose exec postgres psql -U cloudpulse -d cloudpulse -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker compose restart api

# ── Testing & Linting ─────────────────────────────────────────────
test: ## Run backend tests
	python -m pytest tests/ -v

lint: ## Run ruff linter
	ruff check app/ tests/

fmt: ## Auto-format with ruff
	ruff format app/ tests/

# ── SDK ───────────────────────────────────────────────────────────
sdk-install: ## Install the CloudPulse Python SDK locally
	pip install -e sdk/python/

# ── Cleanup ───────────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache dist build *.egg-info

# ── API Shortcuts ─────────────────────────────────────────────────
catalog: ## Fetch the integration catalog
	@curl -s http://localhost:8000/api/v2/integrations/catalog | python3 -m json.tool

integrations: ## List active integrations
	@curl -s http://localhost:8000/api/v2/integrations | python3 -m json.tool

health: ## Check API health
	@curl -s http://localhost:8000/docs > /dev/null && echo "API: OK" || echo "API: DOWN"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: DOWN"
