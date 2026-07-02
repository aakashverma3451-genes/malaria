.PHONY: setup up down logs migrate makemigrations shell test-backend test-frontend lint \
        createsuperuser build ps restart clean minio-init

# ── Setup ─────────────────────────────────────────────────────────────────────
setup:
	@cp -n .env.example .env || true
	@echo "⚠  Edit .env and replace all CHANGE_ME values before continuing."
	docker compose build

# ── Lifecycle ─────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build --no-cache

ps:
	docker compose ps

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f celery-worker

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

makemigrations:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

downgrade:
	docker compose exec backend alembic downgrade -1

# ── MinIO bucket init ─────────────────────────────────────────────────────────
minio-init:
	docker compose exec backend python -m app.scripts.init_minio

# ── Development ───────────────────────────────────────────────────────────────
shell:
	docker compose exec backend python -c "import asyncio; import app.main"

shell-db:
	docker compose exec postgres psql -U $${DB_USER:-malaria} -d $${DB_NAME:-malaria_genomics}

shell-redis:
	docker compose exec redis redis-cli -a $${REDIS_PASSWORD}

# ── Testing ───────────────────────────────────────────────────────────────────
test-backend:
	docker compose exec backend pytest -v --tb=short

test-frontend:
	docker compose exec frontend npm run test

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	docker compose exec backend ruff check app/
	docker compose exec backend ruff format --check app/
	docker compose exec frontend npm run lint

format:
	docker compose exec backend ruff format app/
	docker compose exec backend ruff check --fix app/

# ── Security ──────────────────────────────────────────────────────────────────
audit:
	docker compose exec backend pip-audit -r requirements.txt
	docker compose exec frontend npm audit

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
