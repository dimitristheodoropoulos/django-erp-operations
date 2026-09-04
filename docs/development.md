# Development Guide

This document describes the reproducible development workflow for
`django-erp-operations`.

## 1. Prerequisites

The project targets Python 3.12 and PostgreSQL 16.

Required tools:

- Git
- Python 3.12
- Docker
- Docker Compose

The application dependencies are declared in `pyproject.toml`.

## 2. Environment configuration

Create a local environment file from the provided example:

```bash
cp .env.example .env
```

Review `.env` before starting the application.

For local development, PostgreSQL is normally exposed on port 5432.

## 3. Local Python environment

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the project and test dependencies:

```bash
python -m pip install -e ".[test]"
```

Verify the installed environment:

```bash
python --version
python -m django --version
pytest --version
```

## 4. Start PostgreSQL

Start only the PostgreSQL service:

```bash
docker compose up -d postgres
```

Check service status:

```bash
docker compose ps
```

The PostgreSQL service should report a healthy status.

## 5. Run the Django application locally

With PostgreSQL running, apply migrations:

```bash
python manage.py migrate
```

Run Django system checks:

```bash
python manage.py check
```

Start the development server:

```bash
python manage.py runserver
```

The application is then available at:

```
http://127.0.0.1:8000/
```

Stop the development server with `Ctrl+C`.

## 6. Run the test suite

Run the complete automated test suite:

```bash
pytest -q
```

A successful run should report all tests passing.

## 7. Migration checks

Verify that there are no model changes requiring new migrations:

```bash
python manage.py makemigrations --check --dry-run
```

Inspect migration state:

```bash
python manage.py showmigrations
```

Apply pending migrations when required:

```bash
python manage.py migrate
```

## 8. Django and code quality checks

The repository currently defines the following executable checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python -m compileall apps config tests
pytest -q
```

These checks cover Django configuration, migration consistency,
Python compilation, and the automated test suite.

## 9. Full Docker development environment

Build and start the complete development environment:

```bash
docker compose up --build
```

The web service waits for PostgreSQL to become healthy, applies
Django migrations, and starts the Django development server.

The application is available at:

```
http://127.0.0.1:8000/
```

In another terminal, inspect the services:

```bash
docker compose ps
```

Inspect application logs:

```bash
docker compose logs web
```

Inspect PostgreSQL logs:

```bash
docker compose logs postgres
```

Stop the environment:

```bash
docker compose down
```

To remove the PostgreSQL development volume as well:

```bash
docker compose down -v
```

The `-v` form is destructive to the local PostgreSQL development
database and should only be used when that data can be discarded.

## 10. Reproducibility workflow

For a clean development environment:

```bash
cp .env.example .env
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
docker compose up -d postgres
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python -m compileall apps config tests
pytest -q
```

Alternatively, the complete containerized application environment can
be built and started with:

```bash
docker compose up --build
```

The Docker environment uses Python 3.12 and PostgreSQL 16, matching the
project's declared development targets.

## 11. Management commands

List all available Django management commands:

```bash
python manage.py help
```

For the customer import command:

```bash
python manage.py help import_customers
```

## 12. Shutdown

Stop running Compose services:

```bash
docker compose down
```

The PostgreSQL volume is retained unless `-v` is explicitly supplied.
