# .NET Base Guidelines

**Tech Stack**: .NET 8 LTS, C# 12, ASP.NET Core, Backend Services, Web APIs, Blazor
**Auto-detected from**: `*.csproj`, `*.sln` files
**Version**: 3.0 (Profile-Based Architecture - Principle-Based)
**Last Updated**: 2025-11-16

> **Philosophy**: These guidelines define WHAT and WHY, not HOW. They remain version-agnostic and adaptable across framework versions.

---

## Target Platform

**MUST**:

- Use .NET 8 LTS (Long-Term Support until November 2026)
- Use C# 12 for new projects
- Use ASP.NET Core for web applications and APIs

**Rationale**: .NET 8 LTS provides long-term support with modern features (native AOT, performance improvements, minimal APIs). C# 12 provides collection expressions, primary constructors, and improved pattern matching.

---

## Framework Selection

**Principle**: Choose framework based on project requirements and deployment target

**Options**:

- **ASP.NET Core**: Web APIs, MVC applications (recommended for most web projects)
- **Blazor**: Web UI with C# (Server or WebAssembly)
- **.NET MAUI**: Cross-platform mobile/desktop applications
- **gRPC**: High-performance RPC framework
- **Minimal APIs**: Lightweight HTTP APIs for microservices

**Rationale**: Different frameworks excel at different use cases. ASP.NET Core for comprehensive web features, Blazor for web UI without JavaScript, Minimal APIs for microservices.

---

## Architecture Principles

### Layered Architecture

**MUST** maintain clear separation:

- **Controllers/Endpoints**: Handle HTTP requests/responses, no business logic
- **Services**: Contain business logic, orchestrate operations
- **Repositories**: Handle data access, abstract database operations
- **Models/Entities**: Define business entities
- **DTOs**: Data transfer objects for API contracts

**Rationale**: Layered architecture improves testability, maintainability, and allows independent evolution.

### Dependency Injection

**MUST** use built-in DI container:

- Register services in Program.cs or Startup.cs
- Use constructor injection
- Configure service lifetimes appropriately (Singleton, Scoped, Transient)

**Rationale**: Dependency injection enables testability, loose coupling, and configuration management.

---

## Security Principles

### Input Validation

**MUST**:

- Validate all inputs (request body, query parameters, headers)
- Use FluentValidation or Data Annotations for validation
- Sanitize inputs to prevent injection attacks
- Use model binding with validation attributes

**NEVER**: Trust user input, skip validation

**Rationale**: Input validation prevents security vulnerabilities and data corruption.

### Authentication & Authorization

**MUST**:

- Implement authentication for protected endpoints
- Use ASP.NET Core Identity for user management
- Use industry-standard protocols (OAuth 2.0, OpenID Connect, JWT)
- Implement role-based or policy-based authorization
- Use [Authorize] attribute for endpoint protection

**Rationale**: Security is non-negotiable. ASP.NET Core Identity provides battle-tested authentication.

### SQL Injection Prevention

**MUST**:

- Use Entity Framework Core with parameterized queries
- Use LINQ for database queries
- Never concatenate user input into SQL

**Rationale**: ORM frameworks prevent SQL injection through parameterization.

---

## Database Principles

### ORM Selection

**Options**:

- **Entity Framework Core 8**: Comprehensive ORM, LINQ support (recommended)
- **Dapper**: Lightweight micro-ORM, high performance
- **ADO.NET**: Low-level database access

**Rationale**: EF Core provides type safety, change tracking, and migrations. Dapper for performance-critical scenarios.

### Transaction Management

**MUST**:

- Use transactions for multi-step operations
- Use `TransactionScope` or EF Core transactions
- Handle transaction rollbacks properly

**Rationale**: Transactions ensure data consistency and integrity.

### Migrations

**SHOULD**:

- Use EF Core Migrations for schema changes
- Version all schema changes
- Test migrations in non-production first

**Rationale**: Migrations enable safe schema evolution.

---

## Error Handling Principles

### Exception Handling

**MUST**:

- Use custom exception classes for business errors
- Implement global exception handling middleware
- Log exceptions with context
- Return appropriate HTTP status codes
- Use ProblemDetails (RFC 7807)

**NEVER**: Expose stack traces in production

**Rationale**: Centralized exception handling ensures consistent error responses.

---

## Logging Principles

### Structured Logging

**MUST**:

- Use ILogger<T> from Microsoft.Extensions.Logging
- Use structured logging with named parameters
- Include correlation IDs for request tracing
- Log at appropriate levels (Trace, Debug, Information, Warning, Error, Critical)

**NEVER**: Use Console.WriteLine in production code, log sensitive data

**Rationale**: Structured logging enables efficient searching and filtering.

---

## Testing Principles

### Test Pyramid

**MUST** implement:

- Unit Tests: Test individual classes/methods (70%)
- Integration Tests: Test API endpoints, database (20%)
- E2E Tests: Test critical user flows (10%)

**Target**: 80%+ code coverage on critical paths

**Testing Tools**:

- **xUnit**: Modern testing framework (recommended)
- **NUnit**: Alternative testing framework
- **Moq**: Mocking framework
- **WebApplicationFactory**: Integration testing

**Rationale**: Test pyramid balances speed and confidence.

---

## Performance Principles

### Async Programming

**MUST** use async/await for:

- I/O-bound operations (database, HTTP requests, file I/O)
- Long-running operations
- Concurrent operations

**NEVER**: Use async void (except event handlers), block on async code with .Result or .Wait()

**Rationale**: Async programming improves throughput and prevents thread pool starvation.

### Caching Strategy

**SHOULD** implement caching for:

- Frequently accessed data
- Expensive computations
- External API responses

**Options**: IMemoryCache, IDistributedCache (Redis, SQL Server)

**Rationale**: Caching reduces load and improves response times.

---

## API Design Principles

### RESTful Conventions

**MUST**:

- Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Use plural resource names (/users, not /user)
- Use correct HTTP status codes
- Version APIs (route, query string, or header)
- Implement pagination for collections

**Rationale**: RESTful conventions improve API discoverability.

### Response Format

**MUST**:

- Return consistent response structure
- Use ProblemDetails for errors (RFC 7807)
- Include metadata (timestamps, pagination)

**Rationale**: Consistent responses simplify client implementation.

---

## Deployment Principles

### Build & Packaging

**MUST**:

- Use dotnet publish for deployment
- Publish as self-contained or framework-dependent
- Use AOT compilation for performance-critical apps (.NET 8+)

**Rationale**: Proper packaging ensures deployment consistency.

### Health Checks

**MUST** implement:

- Liveness probe: Is application running?
- Readiness probe: Can application handle requests?
- Include dependency health (database, cache)

**Rationale**: Health checks enable automatic recovery and load balancer integration.

### Environment Configuration

**MUST**:

- Use appsettings.json with environment-specific overrides
- Use User Secrets for local development
- Use environment variables for production
- Validate configuration at startup

**Rationale**: Environment-based configuration enables safe deployments.

---

## Coding Standards

### Naming Conventions

**MUST** follow C# conventions:

- **Classes**: PascalCase (UserService, OrderRepository)
- **Interfaces**: IPascalCase (IUserRepository, IPaymentService)
- **Methods**: PascalCase (GetUserById, ProcessPayment)
- **Variables**: camelCase (userId, orderTotal)
- **Constants**: PascalCase (MaxRetries, DefaultTimeout)
- **Private fields**: _camelCase (_userId, _logger)

**Rationale**: Consistent naming improves code readability.

### Code Organization

**MUST**:

- Keep classes focused and cohesive
- Limit class size (< 500 lines ideal)
- Limit method size (< 50 lines ideal)
- Use meaningful names
- Use XML documentation comments for public APIs

**Rationale**: Well-organized code is easier to understand and maintain.

---

## Observability Principles

### Metrics

**SHOULD** track:

- Request duration and throughput
- Error rates
- Database query performance
- Resource utilization

**Options**: Application Insights, Prometheus, OpenTelemetry

**Rationale**: Metrics enable performance optimization and capacity planning.

### Distributed Tracing

**SHOULD** implement:

- Request correlation IDs
- Activity and trace context propagation
- Integration with tracing systems (Jaeger, Zipkin, Application Insights)

**Rationale**: Distributed tracing enables debugging in microservice architectures.

---

## Dependency Management Principles

### Package Selection

**MUST** evaluate:

- Security (known vulnerabilities)
- Maintenance (last update, active maintainers)
- License compatibility
- Community adoption

**Rationale**: Dependencies become part of your codebase.

### Updates

**SHOULD**:

- Run security audits regularly (dotnet list package --vulnerable)
- Update packages on schedule
- Test updates in non-production first

**Rationale**: Regular updates prevent security vulnerabilities.

---

**Note**: These are principle-based guidelines defining WHAT to do and WHY. Implementation details (HOW) vary by framework version and project requirements. Refer to official documentation for current syntax and APIs.
