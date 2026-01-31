# Python Base Guidelines

**Tech Stack**: Python 3.11/3.12, FastAPI, Django 5, Flask 3, Backend Services, APIs, ML/AI
**Auto-detected from**: `requirements.txt`, `pyproject.toml`, `setup.py`
**Version**: 3.0 (Profile-Based Architecture - Principle-Based)
**Last Updated**: 2025-11-16

> **Philosophy**: These guidelines define WHAT and WHY, not HOW. They remain version-agnostic and adaptable across framework versions.

---

## Target Platform

**MUST**:

- Use Python 3.11+ or Python 3.12+ for new projects
- Use virtual environments (venv, virtualenv, conda, Poetry)
- Use type hints for better code quality and tooling

**Rationale**: Python 3.11+ provides significant performance improvements (10-60% faster) and better error messages. Type hints enable static analysis and IDE support.

---

## Framework Selection

**Principle**: Choose framework based on project requirements and complexity

**Options**:

- **FastAPI**: Modern async framework, automatic API docs, type-based validation (recommended for APIs)
- **Django 5.x**: Full-featured framework, ORM, admin panel, batteries-included (recommended for full-stack)
- **Flask 3.x**: Lightweight, flexible, minimalist (good for microservices)

**Rationale**: Different frameworks excel at different use cases. FastAPI for performance-critical APIs, Django for comprehensive web applications, Flask for simple services.

---

## Architecture Principles

### Code Organization

**MUST** organize by feature/domain rather than technical layer

**Benefits**: Related code stays together, clear module boundaries, scalable architecture.

### Type Hints

**SHOULD** use type hints:

- Function parameters and return types
- Class attributes
- Variable annotations for complex types
- Use mypy or pyright for static type checking

**Rationale**: Type hints improve code documentation, enable better IDE support, and catch type errors before runtime.

---

## Security Principles

### Input Validation

**MUST**:

- Validate all inputs (request body, query parameters, headers)
- Use schema validation (Pydantic, marshmallow, cerberus)
- Sanitize inputs to prevent injection attacks
- Fail fast with clear error messages

**Rationale**: Input validation is the first line of defense. Runtime validation catches issues type hints cannot.

### Authentication & Authorization

**MUST**:

- Implement authentication for protected endpoints
- Use industry-standard protocols (JWT, OAuth 2.0, OpenID Connect)
- Use secure password hashing (bcrypt, argon2, PBKDF2)
- Implement role-based access control (RBAC)

**NEVER**: Store passwords in plain text, use weak hashing algorithms (MD5, SHA1)

**Rationale**: Security is non-negotiable. Using proven patterns prevents common vulnerabilities.

### SQL Injection Prevention

**MUST**:

- Use parameterized queries (SQLAlchemy, Django ORM)
- Never concatenate user input into SQL queries
- Use ORM query builders

**Rationale**: SQL injection is a top security vulnerability. Parameterized queries prevent injection attacks.

---

## Database Principles

### ORM Selection

**Options**:

- **SQLAlchemy**: Flexible ORM, supports multiple databases (PostgreSQL, MySQL, SQLite)
- **Django ORM**: Built-in with Django, declarative models
- **Tortoise ORM**: Async ORM inspired by Django ORM
- **Peewee**: Simple, small footprint ORM

**Rationale**: ORMs provide type safety, prevent SQL injection, and improve developer productivity.

### Data Access Patterns

**MUST**:

- Use parameterized queries
- Implement transactions for multi-step operations
- Use connection pooling
- Include audit fields (created_at, updated_at)
- Implement soft deletes for sensitive data

**Rationale**: These patterns prevent security issues and ensure data integrity.

---

## Error Handling Principles

### Exception Handling

**MUST**:

- Use custom exception classes for business errors
- Implement global exception handlers
- Log exceptions with context
- Return appropriate HTTP status codes
- Hide internal details in production

**NEVER**: Expose stack traces in production, swallow exceptions silently

**Rationale**: Proper exception handling ensures consistent error responses and prevents information leakage.

---

## Logging Principles

### Structured Logging

**MUST**:

- Use structured logging (JSON format)
- Include correlation IDs for request tracing
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Never log sensitive data (passwords, tokens, PII)

**Options**: Python logging module, structlog, loguru

**Rationale**: Structured logs enable efficient searching and filtering. Correlation IDs enable distributed tracing.

---

## Testing Principles

### Test Pyramid

**MUST** implement:

- Unit Tests: Test individual functions/classes (70%)
- Integration Tests: Test API endpoints, database interactions (20%)
- E2E Tests: Test critical user flows (10%)

**Target**: 80%+ code coverage on critical paths

**Testing Tools**:

- **pytest**: Modern testing framework (recommended)
- **unittest**: Standard library testing
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async testing
- **httpx/TestClient**: API testing

**Rationale**: Test pyramid balances speed, confidence, and maintenance cost.

---

## Performance Principles

### Async Programming

**SHOULD** use async/await for:

- I/O-bound operations (database, HTTP requests, file I/O)
- WebSocket connections
- Long-running tasks
- Concurrent operations

**Frameworks**: FastAPI (async-first), aiohttp, asyncio

**Rationale**: Async programming improves throughput for I/O-bound applications.

### Caching Strategy

**SHOULD** implement caching for:

- Frequently accessed data
- Expensive computations
- External API responses

**Options**: Redis, Memcached, in-memory caching (functools.lru_cache)

**Rationale**: Caching reduces load and improves response times.

---

## API Design Principles

### RESTful Conventions

**MUST**:

- Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Use plural resource names (/users, not /user)
- Use correct HTTP status codes
- Version APIs (/v1/users)
- Implement pagination for collections

**Rationale**: RESTful conventions improve API discoverability.

### Response Format

**MUST**:

- Return consistent response structure
- Include metadata (timestamps, pagination)
- Use clear error messages

**Rationale**: Consistent responses simplify client implementation.

---

## Deployment Principles

### Dependency Management

**MUST** use:

- **Poetry**: Modern dependency management (recommended)
- **pip + requirements.txt**: Traditional approach
- **pip-tools**: pip with lock files
- **Pipenv**: Virtual env + dependency management

**MUST**:

- Pin dependency versions
- Use lock files
- Separate dev and production dependencies

**Rationale**: Proper dependency management ensures reproducible builds.

### Process Management

**MUST** use:

- **Gunicorn + Uvicorn**: ASGI server for async apps (FastAPI)
- **Gunicorn**: WSGI server for sync apps (Django, Flask)
- **uWSGI**: Alternative WSGI server
- **Docker**: Containerization

**Rationale**: Proper process management ensures reliability and scalability.

### Health Checks

**MUST** implement:

- Liveness probe: Is application running?
- Readiness probe: Can application handle requests?
- Include dependency health (database, cache)

**Rationale**: Health checks enable automatic recovery and load balancer integration.

---

## Coding Standards

### PEP 8 Style Guide

**MUST** follow PEP 8:

- 4 spaces for indentation
- Maximum line length: 88-100 characters
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

**Tools**: black (formatter), flake8 (linter), isort (import sorting)

**Rationale**: Consistent style improves code readability.

### Code Organization

**MUST**:

- Keep functions small and focused
- Limit file size (< 500 lines ideal)
- Use meaningful names
- Write docstrings for functions and classes
- Comment WHY, not WHAT

**Rationale**: Well-organized code is easier to understand and maintain.

---

## Observability Principles

### Metrics

**SHOULD** track:

- Request duration and throughput
- Error rates
- Database query performance
- Resource utilization (CPU, memory)

**Options**: Prometheus, StatsD, OpenTelemetry

**Rationale**: Metrics enable performance optimization and capacity planning.

### Distributed Tracing

**SHOULD** implement:

- Request correlation IDs
- Trace context propagation
- Integration with tracing systems (Jaeger, Zipkin, OpenTelemetry)

**Rationale**: Distributed tracing enables debugging in microservice architectures.

---

## Dependency Management Principles

### Package Selection

**MUST** evaluate:

- Security (known vulnerabilities)
- Maintenance (last update, active maintainers)
- License compatibility
- Community adoption

**Rationale**: Dependencies become part of your codebase. Choose wisely.

### Updates

**SHOULD**:

- Run security audits regularly (pip-audit, safety)
- Update dependencies on schedule
- Test updates in non-production first

**Rationale**: Regular updates prevent accumulation of security vulnerabilities.

---

**Note**: These are principle-based guidelines defining WHAT to do and WHY. Implementation details (HOW) vary by framework version and project requirements. Refer to official documentation for current syntax and APIs.
