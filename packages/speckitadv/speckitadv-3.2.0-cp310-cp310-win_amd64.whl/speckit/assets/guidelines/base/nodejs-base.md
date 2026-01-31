# Node.js Base Guidelines

**Tech Stack**: Node.js 20/22 LTS, TypeScript 5+, Express/Fastify/NestJS, Backend Services, APIs
**Auto-detected from**: `package.json` with backend dependencies
**Version**: 3.0 (Profile-Based Architecture - Principle-Based)
**Last Updated**: 2025-11-16

> **Philosophy**: These guidelines define WHAT and WHY, not HOW. They remain version-agnostic and adaptable across framework versions.

---

## Target Platform

**MUST**:

- Use Node.js LTS versions (20 LTS or 22 LTS)
- Use TypeScript for all new projects
- Target ES2022 or ESNext for modern JavaScript features

**Rationale**: LTS versions provide 3 years active support plus 18 months maintenance. TypeScript ensures type safety, better tooling, and maintainability.

---

## Framework Selection

**Principle**: Choose framework based on project requirements, team expertise, and performance needs

**Options**:

- **Express**: Most popular, largest ecosystem, traditional middleware approach
- **Fastify**: High performance (3x faster than Express), schema validation, plugin architecture
- **NestJS**: TypeScript-first, dependency injection, Angular-inspired, ideal for large teams
- **Koa**: Minimalist, async/await-first design
- **Hapi**: Configuration-driven, enterprise features

**Recommendation**: Use Fastify for performance-critical APIs, NestJS for enterprise applications with large teams, Express for standard projects with rich ecosystem needs.

**Rationale**: Different frameworks excel in different scenarios. Performance, developer experience, and ecosystem maturity should guide selection.

---

## Architecture Principles

### Separation of Concerns

**MUST** maintain clear boundaries:

- **Controllers**: Handle HTTP requests/responses only, no business logic
- **Services**: Contain business logic, orchestrate operations
- **Repositories**: Handle data access, abstract database operations
- **Models**: Define data structures and validation rules
- **Middleware**: Handle cross-cutting concerns (logging, authentication, error handling)

**Rationale**: Clear separation improves testability, maintainability, and allows independent evolution of each layer.

### Project Structure

**MUST** organize by feature/domain rather than technical layer:

**Benefits**:

- Related code stays together
- Easy to locate functionality
- Clear module boundaries
- Scalable for large applications
- Supports microservices extraction

**Rationale**: Domain-driven organization scales better than layered organization as applications grow.

---

## Security Principles

### Input Validation

**MUST**:

- Validate ALL inputs (request body, query parameters, headers, path parameters)
- Use schema validation libraries (Zod, Joi, class-validator)
- Sanitize inputs to prevent injection attacks
- Fail fast with clear error messages

**NEVER**:

- Trust user input
- Skip validation for "internal" APIs
- Use client-side validation only

**Rationale**: Input validation is the first line of defense against attacks. Runtime validation catches issues TypeScript cannot.

### Authentication & Authorization

**MUST**:

- Implement authentication for protected endpoints
- Use industry-standard protocols (JWT, OAuth 2.0, OpenID Connect)
- Store passwords using strong hashing (bcrypt, argon2)
- Implement role-based access control (RBAC)
- Use httpOnly, secure, sameSite cookies for tokens

**NEVER**:

- Store passwords in plain text
- Use weak hashing algorithms (MD5, SHA1)
- Store tokens in localStorage (XSS vulnerability)
- Implement custom cryptography

**Rationale**: Security is non-negotiable. Using proven patterns prevents common vulnerabilities.

### Secrets Management

**MUST**:

- Use environment variables for secrets
- Never commit secrets to version control
- Validate environment variables at startup
- Use different secrets per environment
- Rotate secrets regularly

**Rationale**: Hardcoded secrets lead to breaches. Environment-based configuration enables secure deployment.

### Rate Limiting

**MUST** implement:

- Per-IP rate limiting
- Per-user rate limiting
- Different limits for different endpoints
- Clear error messages when limits exceeded

**Rationale**: Rate limiting prevents abuse, DoS attacks, and ensures fair resource usage.

---

## Database Principles

### ORM Selection

**MUST** choose based on requirements:

- **Prisma**: Type-safe, excellent developer experience, automatic migrations
- **TypeORM**: Mature, supports multiple databases, Active Record or Data Mapper patterns
- **Drizzle**: Lightweight, SQL-like syntax, performant
- **Mongoose**: MongoDB-specific, schema-based, rich plugin ecosystem

**Rationale**: ORMs provide type safety, prevent SQL injection, and improve developer productivity.

### Data Access Patterns

**MUST**:

- Use parameterized queries (never string concatenation)
- Implement transactions for multi-step operations
- Use connection pooling
- Include audit fields (createdAt, updatedAt, createdBy, updatedBy)
- Implement soft deletes for sensitive data

**SHOULD**:

- Use migrations for schema changes
- Version your database schema
- Test migrations in staging before production

**Rationale**: These patterns prevent security issues, ensure data integrity, and enable safe schema evolution.

---

## Error Handling Principles

### Centralized Error Handling

**MUST**:

- Implement global error handler
- Use custom error classes for different error types
- Log errors with context
- Return appropriate HTTP status codes
- Hide internal details in production

**NEVER**:

- Expose stack traces in production
- Return database errors directly to clients
- Silently swallow errors

**Rationale**: Centralized handling ensures consistent error responses and prevents information leakage.

### Error Classification

**MUST** distinguish:

- **Operational Errors**: Expected errors (validation, not found, unauthorized)
- **Programming Errors**: Bugs (null reference, type errors)
- **Infrastructure Errors**: Database down, network failures

**Rationale**: Different error types require different handling strategies.

---

## Logging Principles

### Structured Logging

**MUST**:

- Use structured logging (JSON format)
- Include correlation IDs for request tracing
- Log at appropriate levels (debug, info, warn, error, fatal)
- Include relevant context (userId, requestId, operation)

**NEVER**:

- Log sensitive data (passwords, tokens, PII, credit cards)
- Use console.log in production
- Log excessive information in hot paths

**Rationale**: Structured logs enable efficient searching, filtering, and analysis. Correlation IDs enable distributed tracing.

### Log Levels

**Guidelines**:

- **debug**: Development debugging, verbose details
- **info**: Normal operations, significant events
- **warn**: Warning conditions, degraded performance
- **error**: Error conditions requiring attention
- **fatal**: Critical errors causing shutdown

**Rationale**: Appropriate log levels enable effective filtering and alerting.

---

## Testing Principles

### Test Pyramid

**MUST** implement:

- **Unit Tests**: Test individual functions/classes (70% of tests)
- **Integration Tests**: Test API endpoints, database interactions (20% of tests)
- **E2E Tests**: Test critical user flows (10% of tests)

**Target**: 80%+ code coverage on critical paths

**Rationale**: Test pyramid balances speed, confidence, and maintenance cost.

### Testing Practices

**MUST**:

- Test behavior, not implementation
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Test error cases and edge cases

**Rationale**: Well-tested code reduces bugs, enables refactoring, and serves as documentation.

---

## Performance Principles

### Async Operations

**MUST**:

- Use async/await for I/O operations
- Never block the event loop
- Handle Promise rejections
- Use Promise.all() for parallel operations

**Rationale**: Non-blocking I/O is Node.js's strength. Blocking operations degrade performance.

### Caching Strategy

**SHOULD** implement caching for:

- Frequently accessed data
- Expensive computations
- External API responses

**Options**:

- In-memory caching (node-cache)
- Distributed caching (Redis)
- HTTP caching (ETags, Cache-Control)

**Rationale**: Caching reduces load, improves response times, and lowers costs.

### Connection Pooling

**MUST**:

- Configure database connection pools
- Set appropriate min/max connections
- Handle connection errors gracefully
- Monitor pool utilization

**Rationale**: Connection pooling improves performance and prevents resource exhaustion.

---

## API Design Principles

### RESTful Conventions

**MUST**:

- Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Use plural resource names (`/users`, not `/user`)
- Use correct HTTP status codes
- Version APIs (`/v1/users`)
- Implement pagination for collections

**Rationale**: RESTful conventions improve API discoverability and client integration.

### Response Format

**MUST**:

- Return consistent response structure
- Include metadata (timestamps, pagination info)
- Use clear error messages
- Follow JSON:API or similar specification

**Rationale**: Consistent responses simplify client implementation.

---

## Deployment Principles

### Process Management

**MUST**:

- Use process manager (PM2, systemd, Docker, Kubernetes)
- Implement graceful shutdown
- Handle SIGTERM/SIGINT signals
- Close connections cleanly

**Rationale**: Proper shutdown prevents data loss and connection leaks.

### Health Checks

**MUST** implement:

- **Liveness probe**: Is process running?
- **Readiness probe**: Can process handle requests?
- Include dependency health (database, cache, external services)

**Rationale**: Health checks enable automatic recovery and load balancer integration.

### Environment Configuration

**MUST**:

- Use environment-specific configuration
- Validate configuration at startup
- Fail fast on missing required configuration
- Support multiple environments (dev, staging, production)

**Rationale**: Environment-based configuration enables safe deployments across environments.

---

## TypeScript Configuration Principles

**MUST** enable:

- `strict`: Enable all strict type checking
- `noUncheckedIndexedAccess`: Prevent undefined access bugs
- `esModuleInterop`: Enable CommonJS/ESM interop
- `skipLibCheck`: Skip type checking of declaration files (build speed)
- `forceConsistentCasingInFileNames`: Prevent cross-platform issues

**Rationale**: Strict TypeScript configuration catches bugs at compile time.

---

## Coding Standards

### Naming Conventions

**MUST** follow:

- **Files**: kebab-case (`user-service.ts`)
- **Classes**: PascalCase (`UserService`)
- **Functions/Variables**: camelCase (`getUserById`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Interfaces**: PascalCase (`UserRepository` or `IUserRepository`)

**Rationale**: Consistent naming improves code readability and reduces cognitive load.

### Code Organization

**MUST**:

- Keep functions small and focused
- Limit file size (< 300 lines ideal)
- Group related functionality
- Use meaningful variable names
- Comment WHY, not WHAT

**Rationale**: Well-organized code is easier to understand, test, and maintain.

---

## Observability Principles

### Metrics

**SHOULD** track:

- Request duration and throughput
- Error rates
- Database query performance
- External API latency
- Resource utilization (CPU, memory)

**Rationale**: Metrics enable performance optimization and capacity planning.

### Distributed Tracing

**SHOULD** implement:

- Request correlation IDs
- Trace context propagation
- Span creation for operations
- Integration with tracing systems (Jaeger, Zipkin, OpenTelemetry)

**Rationale**: Distributed tracing enables debugging in microservice architectures.

---

## Dependency Management

### Package Selection

**MUST** evaluate:

- Security (known vulnerabilities)
- Maintenance (last update, active maintainers)
- License compatibility
- Bundle size impact
- TypeScript support

**Rationale**: Dependencies become part of your codebase. Choose wisely.

### Updates

**SHOULD**:

- Run security audits regularly (`npm audit`)
- Update dependencies on schedule
- Test updates in non-production first
- Use lock files (package-lock.json)

**Rationale**: Regular updates prevent accumulation of security vulnerabilities.

---

**Note**: These are principle-based guidelines defining WHAT to do and WHY. Implementation details (HOW) vary by framework version and project requirements. Refer to official documentation for current syntax and APIs.
