# TESTING
.PHONY: test-all test-unit test-integration test-e2e

test-all: test-unit test-integration test-e2e

test-unit:
	docker compose run --rm --no-deps --entrypoint=pytest app -q tests/unit

test-integration:
	make compose-run-redis
	docker compose run --rm --no-deps --entrypoint=pytest app -q tests/integration
	make compose-down

test-e2e:
	make compose-run-redis
	docker compose run --rm --no-deps --entrypoint=pytest app -q tests/e2e
	make compose-down


# DJANGO STUFF
.PHONY: django-makemigrations django-migrate django-shell django-runserver

DJANGO_PROJECT_DIR = src/dddjango
MANAGE = $(DJANGO_PROJECT_DIR)/manage.py

django-makemigrations:
	@python $(MANAGE) makemigrations

django-migrate:
	@python $(MANAGE) migrate

django-shell:
	@python $(MANAGE) shell

django-runserver:
	@python $(MANAGE) runserver 0.0.0.0:8000

django-up: django-makemigrations django-migrate django-runserver


# DOCKER STUFF
.PHONY: compose-build compose-up compose-down compose-run-redis

compose-build:
	docker compose build

compose-up: compose-build
	docker compose -d up

compose-down:
	docker compose down --remove-orphans

compose-run-redis:
	docker compose up -d redis
