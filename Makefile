.PHONY: test
test:
	pytest -q

.PHONY: django_makemigrations django_migrate django_shell django_runserver

DJANGO_PROJECT_DIR = src/dddjango
MANAGE = $(DJANGO_PROJECT_DIR)/manage.py

django_makemigrations:
	@python $(MANAGE) makemigrations

django_migrate:
	@python $(MANAGE) migrate

django_shell:
	@python $(MANAGE) shell

django_runserver:
	@python $(MANAGE) runserver 0.0.0.0:8000
