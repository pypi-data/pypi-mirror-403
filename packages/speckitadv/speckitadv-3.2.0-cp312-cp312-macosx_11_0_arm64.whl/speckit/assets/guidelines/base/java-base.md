# Java Base Guidelines

**Tech Stack**: Java 21 LTS, Spring Boot 3.2+, Maven/Gradle, Backend Services, Microservices
**Auto-detected from**: `pom.xml`, `build.gradle`, or `build.gradle.kts`
**Version**: 3.0 (Profile-Based Architecture - Principle-Based)
**Last Updated**: 2025-11-16

> **Philosophy**: These guidelines define WHAT and WHY, not HOW. They remain version-agnostic and adaptable across framework versions.

---

## Target Platform

**MUST**:

- Use Java 21 LTS (Long-Term Support until September 2028)
- Use Spring Boot 3.2+ or equivalent framework for new projects
- Use Maven 3.9+ or Gradle 8.5+ for build automation

**Rationale**: Java 21 LTS provides long-term support with modern features (virtual threads, pattern matching, records, sealed classes). Spring Boot 3.2+ requires Java 17+ and provides production-ready features.

---

## Framework Selection

**Principle**: Choose framework based on project requirements, deployment target, and performance needs

**Options**:

- **Spring Boot 3.2+**: Enterprise-grade, comprehensive ecosystem, battle-tested (recommended for most projects)
- **Quarkus 3.x**: Cloud-native, fast startup time, low memory footprint, Kubernetes-optimized
- **Micronaut 4.x**: Lightweight, compile-time dependency injection, fast startup, low memory

**Rationale**: Different frameworks excel in different scenarios. Spring Boot for comprehensive features and ecosystem, Quarkus/Micronaut for cloud-native and resource-constrained environments.

---

## Architecture Principles

### Layered Architecture

**MUST** maintain clear separation:

- **Controllers/Resources**: Handle HTTP requests/responses, no business logic
- **Services**: Contain business logic, orchestrate operations
- **Repositories**: Handle data access, abstract database operations
- **Domain Models**: Define business entities and validation rules
- **DTOs**: Transfer objects for API contracts

**Rationale**: Layered architecture improves testability, maintainability, and allows independent evolution of each layer.

### SOLID Principles

**MUST** follow:

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable for base types
- **Interface Segregation**: Many specific interfaces better than one general
- **Dependency Inversion**: Depend on abstractions, not concretions

**Rationale**: SOLID principles improve code maintainability, testability, and flexibility.

### Dependency Injection

**MUST** use:

- Framework-provided dependency injection (Spring, CDI, Quarkus DI, Micronaut DI)
- Constructor injection (preferred over field injection)
- Interface-based dependencies

**NEVER**:

- Use `new` operator for service dependencies
- Use field injection in production code (harder to test)
- Create circular dependencies

**Rationale**: Dependency injection enables testability, loose coupling, and flexibility.

---

## Security Principles

### Input Validation

**MUST**:

- Validate all inputs (request body, query parameters, headers, path variables)
- Use Bean Validation (Jakarta Validation) for declarative validation
- Sanitize inputs to prevent injection attacks
- Fail fast with clear error messages

**NEVER**:

- Trust user input
- Skip validation for "internal" APIs
- Use client-side validation only

**Rationale**: Input validation is the first line of defense against attacks. Server-side validation is security-critical.

### Authentication & Authorization

**MUST**:

- Implement authentication for protected endpoints
- Use industry-standard protocols (OAuth 2.0, OpenID Connect, JWT, SAML)
- Use strong password hashing (BCrypt, Argon2, PBKDF2)
- Implement role-based access control (RBAC) or attribute-based access control (ABAC)
- Use method-level security annotations

**NEVER**:

- Store passwords in plain text
- Use weak hashing algorithms (MD5, SHA1)
- Implement custom cryptography
- Skip authorization checks

**Rationale**: Security is non-negotiable. Using proven security patterns prevents common vulnerabilities.

### SQL Injection Prevention

**MUST**:

- Use parameterized queries (JPA, JDBC PreparedStatement)
- Use ORM frameworks (Hibernate, JPA) properly
- Validate and sanitize all SQL inputs

**NEVER**:

- Concatenate user input into SQL queries
- Use String.format() or StringBuilder for SQL queries
- Disable ORM query sanitization

**Rationale**: SQL injection is a top security vulnerability. Parameterized queries prevent injection attacks.

---

## Database Principles

### ORM Selection

**MUST** choose based on requirements:

- **JPA/Hibernate**: Standard ORM, comprehensive features, wide adoption
- **jOOQ**: Type-safe SQL, fine-grained control, complex queries
- **MyBatis**: SQL-focused, flexible mapping
- **Spring Data JPA**: Simplified repository pattern, query derivation

**Rationale**: ORMs provide type safety, prevent SQL injection, and improve developer productivity.

### Transaction Management

**MUST**:

- Use declarative transactions (@Transactional)
- Define transaction boundaries at service layer
- Configure appropriate isolation levels
- Handle transaction rollbacks properly
- Use read-only transactions for queries

**Rationale**: Proper transaction management ensures data consistency and integrity.

### Connection Pooling

**MUST**:

- Use connection pooling (HikariCP recommended)
- Configure pool size appropriately
- Set connection timeouts
- Monitor pool utilization
- Handle connection leaks

**Rationale**: Connection pooling improves performance and prevents resource exhaustion.

### Database Migrations

**SHOULD**:

- Use migration tools (Flyway, Liquibase)
- Version all schema changes
- Test migrations in non-production first
- Maintain rollback scripts
- Include migrations in version control

**Rationale**: Migration tools enable safe schema evolution and environment consistency.

---

## Error Handling Principles

### Exception Hierarchy

**MUST**:

- Use custom exception classes for business errors
- Extend appropriate base exceptions
- Provide meaningful error messages
- Include error codes for client handling

**Exception Types**:

- **Checked Exceptions**: Recoverable errors (business validation)
- **Unchecked Exceptions**: Programming errors (NullPointerException, IllegalArgumentException)
- **Custom Business Exceptions**: Domain-specific errors

**Rationale**: Proper exception hierarchy improves error handling and debugging.

### Global Exception Handling

**MUST**:

- Implement global exception handler (@ControllerAdvice, ExceptionMapper)
- Return appropriate HTTP status codes
- Hide internal details in production
- Log exceptions with context

**NEVER**:

- Expose stack traces to clients in production
- Return database errors directly to clients
- Swallow exceptions silently

**Rationale**: Centralized exception handling ensures consistent error responses and prevents information leakage.

---

## Logging Principles

### Structured Logging

**MUST**:

- Use SLF4J as logging facade
- Use Logback or Log4j2 as implementation
- Use structured logging (JSON format in production)
- Include correlation IDs for request tracing
- Log at appropriate levels (DEBUG, INFO, WARN, ERROR)

**NEVER**:

- Use System.out.println() in production code
- Log sensitive data (passwords, tokens, PII, credit cards)
- Log excessive information in hot paths

**Rationale**: Structured logs enable efficient searching and filtering. SLF4J provides abstraction over logging implementations.

### Log Levels

**Guidelines**:

- **DEBUG**: Development debugging, verbose details
- **INFO**: Normal operations, significant events
- **WARN**: Warning conditions, degraded performance
- **ERROR**: Error conditions requiring attention
- **FATAL**: Critical errors causing shutdown

**Rationale**: Appropriate log levels enable effective filtering and alerting.

---

## Testing Principles

### Test Pyramid

**MUST** implement:

- **Unit Tests**: Test individual classes/methods (70% of tests)
- **Integration Tests**: Test API endpoints, database interactions (20% of tests)
- **E2E Tests**: Test critical user flows (10% of tests)

**Target**: 80%+ code coverage on critical paths

**Rationale**: Test pyramid balances speed, confidence, and maintenance cost.

### Testing Practices

**MUST**:

- Use JUnit 5 for unit tests
- Use Mockito for mocking dependencies
- Use Spring Boot Test for integration tests
- Use Test containers for database testing
- Follow AAA pattern (Arrange, Act, Assert)
- Test behavior, not implementation

**Rationale**: Well-tested code reduces bugs, enables refactoring, and serves as documentation.

---

## Performance Principles

### Async Processing

**SHOULD** use for:

- Long-running operations
- I/O-bound tasks
- Parallel processing

**Options**:

- CompletableFuture for async programming
- Spring @Async for asynchronous methods
- Virtual Threads (Java 21+) for massive concurrency
- Reactive programming (Spring WebFlux, Reactor)

**Rationale**: Async processing improves throughput and resource utilization.

### Caching Strategy

**SHOULD** implement caching for:

- Frequently accessed data
- Expensive computations
- External API responses

**Options**:

- Spring Cache abstraction
- Caffeine (in-memory caching)
- Redis (distributed caching)
- EHCache (multi-level caching)

**Rationale**: Caching reduces load, improves response times, and lowers costs.

### JVM Tuning

**SHOULD** configure:

- Appropriate heap size (-Xms, -Xmx)
- Garbage collector selection (G1GC, ZGC, Shenandoah)
- JVM flags for performance and observability
- Monitor GC logs and metrics

**Rationale**: Proper JVM tuning improves performance and prevents OutOfMemoryErrors.

---

## API Design Principles

### RESTful Conventions

**MUST**:

- Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Use plural resource names (/users, not /user)
- Use correct HTTP status codes
- Version APIs (/v1/users)
- Implement pagination for collections
- Use HATEOAS for discoverability (optional)

**Rationale**: RESTful conventions improve API discoverability and client integration.

### Response Format

**MUST**:

- Return consistent response structure
- Include metadata (timestamps, pagination info)
- Use clear error messages
- Follow standard specifications (JSON:API, Problem Details RFC 7807)

**Rationale**: Consistent responses simplify client implementation.

---

## Deployment Principles

### Build & Packaging

**MUST**:

- Build executable JARs (Spring Boot fat JARs)
- Include all dependencies
- Externalize configuration
- Use multi-stage Docker builds

**Rationale**: Executable JARs simplify deployment and reduce dependencies.

### Health Checks

**MUST** implement:

- **Liveness probe**: Is application running?
- **Readiness probe**: Can application handle requests?
- Include dependency health (database, cache, external services)

**Rationale**: Health checks enable automatic recovery and load balancer integration.

### Environment Configuration

**MUST**:

- Use environment-specific configuration (application-{profile}.properties/yml)
- Externalize configuration (environment variables, config servers)
- Validate configuration at startup
- Fail fast on missing required configuration

**Rationale**: Environment-based configuration enables safe deployments across environments.

---

## Coding Standards

### Naming Conventions

**MUST** follow Java conventions:

- **Classes**: PascalCase (UserService, OrderRepository)
- **Interfaces**: PascalCase (UserRepository, PaymentService)
- **Methods**: camelCase (getUserById, processPayment)
- **Variables**: camelCase (userId, orderTotal)
- **Constants**: UPPER_SNAKE_CASE (MAX_RETRIES, DEFAULT_TIMEOUT)
- **Packages**: lowercase (com.yourorg.service.user)

**Rationale**: Consistent naming improves code readability.

### Code Organization

**MUST**:

- Keep classes focused and cohesive
- Limit class size (< 500 lines ideal)
- Limit method size (< 50 lines ideal)
- Use meaningful names
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
- Resource utilization (CPU, memory, threads)
- Business metrics (orders processed, payments completed)

**Options**:

- Micrometer (abstraction layer)
- Prometheus (metrics storage)
- Grafana (visualization)

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
- Size impact on build artifacts
- Community adoption

**Rationale**: Dependencies become part of your codebase. Choose wisely.

### Updates

**SHOULD**:

- Run security audits regularly (mvn dependency:check, gradle dependencyCheckAnalyze)
- Update dependencies on schedule
- Test updates in non-production first
- Use dependency lock files

**Rationale**: Regular updates prevent accumulation of security vulnerabilities.

---

**Note**: These are principle-based guidelines defining WHAT to do and WHY. Implementation details (HOW) vary by framework version and project requirements. Refer to official documentation for current syntax and APIs.
