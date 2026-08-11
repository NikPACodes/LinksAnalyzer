CELERY_QUEUE ?= analyzer
CELERY_CONCURRENCY ?= 1

ALEMBIC_MESSAGE ?= migration
ALEMBIC_REVISION ?= -1

# Docker
.PHONY: docker-build docker-up docker-up-d \
		docker-down docker-clean docker-restart \
		docker-logs docker-logs-worker \
		docker-ps docker-bash

# Docker Alembic
.PHONY: docker-alembic-current docker-alembic-history docker-alembic-heads \
		docker-migrate docker-migrate-down docker-migrate-revision migrate-auto

# Local
.PHONY: install install-dev run-local worker-local

# Alembic Local
.PHONY: alembic-current alembic-history alembic-heads \
		migrate migrate-down migrate-revision migrate-auto

#--------------------------
# Docker
#--------------------------
docker-build:
	docker compose build

docker-up:
	docker compose up

docker-up-d:
	docker compose up -d

docker-down:
	docker compose down

docker-clean:
	docker compose down -v

docker-restart:
	docker compose down
	docker compose up -d --build

docker-logs:
	docker compose logs -f app

docker-logs-worker:
	docker compose logs -f worker

docker-ps:
	docker compose ps

docker-bash:
	docker compose exec app bash


#--------------------------
# Docker Alembic
#--------------------------
docker-alembic-current:
	docker compose exec app alembic current

docker-alembic-history:
	docker compose exec app alembic history

docker-alembic-heads:
	docker compose exec app alembic heads

# Применить все миграции
docker-migrate:
	docker compose exec app alembic upgrade head

# Откат на N миграцию назад
docker-migrate-down:
	docker compose exec app alembic downgrade "$(ALEMBIC_REVISION)"

# Создание пустой миграции
docker-migrate-revision:
	docker compose exec app alembic revision -m "$(ALEMBIC_MESSAGE)"

# Авто создание миграции
docker-migrate-auto:
	docker compose exec app alembic revision --autogenerate -m "$(ALEMBIC_MESSAGE)"


#--------------------------
# Local
#--------------------------
install:
	python -m pip install --upgrade pip
	python -m pip install "."

install-dev:
	python -m pip install --upgrade pip
	python -m pip install ".[dev]"

run-local:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker-local:
	celery -A app.worker.celery_app.celery_app worker --loglevel=info --queues=$(CELERY_QUEUE) --concurrency=$(CELERY_CONCURRENCY)

#--------------------------
# Alembic Local
#--------------------------
alembic-current:
	alembic current

alembic-history:
	alembic history

alembic-heads:
	alembic heads

# Применить все миграции
migrate:
	upgrade head

# Откат на N миграцию назад
migrate-down:
	alembic downgrade "$(ALEMBIC_REVISION)"

# Создание пустой миграции
migrate-revision:
	alembic revision -m "$(ALEMBIC_MESSAGE)"

# Авто создание миграции
migrate-auto:
	alembic revision --autogenerate -m "$(ALEMBIC_MESSAGE)"