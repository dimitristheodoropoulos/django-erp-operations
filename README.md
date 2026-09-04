# Django ERP Operations

A production-oriented Django ERP portfolio project focused on
operational business workflows, relational data modelling,
order lifecycle management, REST APIs, automated testing,
Dockerized development, and CI.

## Project Overview

This project demonstrates how a business-oriented ERP backend can
be designed and implemented using Python and Django.

The focus is not simply on CRUD functionality, but on separating
domain models, business rules, transactional services, API
interfaces, permissions, error handling, testing, and development
infrastructure.

The project is developed incrementally through requirement-driven
milestones, with implementation and verification evidence maintained
alongside the codebase.

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL 16
- pytest
- Docker
- Docker Compose
- GitHub Actions
- Git

## Current Capabilities

### Domain and Business Logic

- Customer and sales-order domain modelling
- Sales-order lifecycle management
- Transactional business services
- Business-rule enforcement
- Explicit domain exceptions
- Stock-related validation during order lifecycle operations

### REST API

- Versioned REST API
- Sales-order lifecycle endpoints
- Permission enforcement
- Serializer-based responses
- Structured API error responses
- Explicit mapping between domain exceptions and HTTP responses

### Database

- PostgreSQL-backed Django application
- Relational data modelling
- Django ORM
- Django migrations
- Migration consistency verification
- Transactional database operations

### Testing and Verification

The project uses automated testing as part of the development
workflow.

The current containerized environment has been verified with:

- Django system checks
- Migration consistency checks
- Python compilation checks
- Full pytest regression
- PostgreSQL-backed integration testing
- GitHub Actions CI

Current containerized regression:

**181 tests passed.**

## Architecture

The application follows a layered approach that keeps HTTP concerns
separate from business logic.

```text
HTTP Request
     |
     v
API View
     |
     v
Permissions
     |
     v
Domain Service
     |
     v
Transactional Business Logic
     |
     v
Django ORM
     |
     v
PostgreSQL
````

This separation allows the same business rules to be exercised
independently from the HTTP interface.

## Development Environment

The project provides both local and Docker-based development
workflows.

The Docker environment includes:

```text
Django application
        |
        v
   PostgreSQL 16
```

Docker Compose provides the application and database services,
including PostgreSQL health checks and Django startup/migration
handling.

See:

* `docs/development.md`
* `docs/architecture.md`
* `docs/database.md`
* `docs/api.md`
* `docs/traceability.md`

## CI

GitHub Actions provides automated checks for pushes and pull requests.

The CI pipeline currently performs:

1. Python environment setup
2. PostgreSQL service startup
3. Project/test dependency installation
4. Django migrations
5. Django system checks
6. Migration consistency checks
7. Python compilation
8. Full pytest regression

## Requirements Traceability

The project uses requirement-driven development and maintains
traceability between requirements, implementation, documentation,
and verification evidence.

See:

`docs/traceability.md`

## Project Status

This is an active portfolio engineering project under incremental
development.

Completed milestones represent implemented and verified functionality.
Additional functionality is intentionally developed in subsequent
milestones rather than being presented as already complete.

## Scope

The project currently focuses on backend ERP operations and software
engineering practices.

It does not claim:

* Production deployment validation
* Physical hardware validation
* Production ERP customer deployment
* Odoo implementation
* Functional-safety certification
* Large-scale production load validation

## Why This Project

The project is designed to demonstrate practical engineering skills
relevant to business and ERP software development:

* Python
* Django
* Django ORM
* PostgreSQL
* REST APIs
* Business logic
* Transactions
* Permissions
* Error handling
* Automated testing
* Docker
* CI/CD
* Git
* Requirement traceability
  EOF

````

### Βήμα 2 — Δημιούργησε το LICENSE

```bash
cat > LICENSE <<'EOF'
MIT License

Copyright (c) 2026 Dimitris Theodoropoulos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
