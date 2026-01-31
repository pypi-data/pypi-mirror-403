# Node.js Corporate Profile Overrides

**Profile**: Corporate
**Stack**: Node.js
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only corporate-specific overrides. Base guidelines are inherited from `base/nodejs-base.md`.
> **Philosophy**: These overrides define WHAT corporate Node.js projects require and WHY, not HOW to implement them.

---

## Scaffolding Principles

**MUST** use corporate-approved scaffolding:

- Use organization's scaffolding tools (typically `@YOUR_ORG/create-node-service`)
- Choose template based on architecture (Express, Fastify, NestJS, minimal API, microservice, GraphQL, gRPC)
- Scaffolding includes pre-configured security, logging, monitoring, compliance, observability

**NEVER**:

- Use public scaffolding tools or generators without security review
- Start from scratch without corporate starter templates

**Rationale**: Corporate scaffolding ensures security baselines, compliance requirements, and observability from day one. Prevents common security gaps and reduces setup time.

---

## Package Registry Principles

**MUST** use corporate package registry exclusively:

- Configure npm/yarn/pnpm to use corporate registry (Artifactory, Nexus, Azure Artifacts, GitHub Packages)
- All dependencies resolved through corporate registry only
- Use authentication tokens from environment variables (never hardcoded)
- Configure scoped packages for organization namespace

**NEVER**:

- Install packages directly from public npmjs.org without security scanning
- Commit authentication credentials to version control
- Use plaintext passwords in configuration

**Configuration Requirements**:

- Place `.npmrc` or `.yarnrc.yml` at project root
- Use environment variables for CI/CD authentication
- Configure package scopes per organization policy

**Rationale**: Corporate registries provide security scanning, vulnerability detection, license compliance, and audit trails. Public packages may contain malicious code or licensing issues.

---

## Mandatory Corporate Libraries

### Framework Starter

**MUST** use organization's framework starter:

- Use corporate starter package (typically `@YOUR_ORG/express-starter`, `@YOUR_ORG/fastify-starter`, or `@YOUR_ORG/nestjs-starter`)
- Includes pre-configured security middleware, logging, metrics, error handling, CORS, rate limiting, health checks, observability
- TypeScript-first configuration

**Benefits**:

- Security middleware out-of-the-box
- Consistent application structure
- Compliance requirements pre-configured
- Observability integrated
- Reduced boilerplate

**NEVER**:

- Build custom server setup from scratch
- Use public starter templates without approval

**Rationale**: Corporate starters ensure consistent security posture, logging, monitoring, and compliance across all Node.js services.

---

### Authentication & Authorization

**MUST** use organization's auth middleware:

- Use corporate auth package (typically `@YOUR_ORG/auth-middleware`)
- Apply authentication globally or per-route
- Support role-based access control (RBAC)
- Extract authenticated user from request context
- Support multiple auth methods (JWT, OAuth 2.0, API keys, mutual TLS)

**Requirements**:

- Validate all protected endpoints
- Log authentication attempts (success and failure)
- Support corporate identity providers (Azure AD, Okta, corporate SSO, LDAP/Active Directory)
- Handle token refresh automatically
- Implement multi-factor authentication (MFA) when required

**NEVER**:

- Implement custom authentication without security review
- Skip authorization checks on "internal" routes
- Store tokens insecurely
- Use public auth libraries without approval

**Rationale**: Authentication is security-critical. Corporate libraries ensure consistent security posture, compliance with identity policies, and integration with corporate identity systems.

---

### API Client & Resilience

**MUST** use organization's API client:

- Use corporate API client package (typically `@YOUR_ORG/api-client`)
- Configure timeout, retry logic with exponential backoff, and circuit breaker pattern
- Never use raw HTTP clients (axios, fetch, got, undici) directly
- Auto-instrumented for distributed tracing

**Requirements**:

- Configure appropriate timeouts per service
- Implement retry logic for transient failures
- Use circuit breaker to prevent cascade failures
- Handle errors gracefully
- Include correlation IDs for request tracing

**Features**:

- Automatic request/response logging
- Automatic metrics collection
- Connection pooling
- Request deduplication
- Load balancing support

**NEVER**:

- Use raw HTTP clients without corporate wrapper
- Skip error handling
- Implement custom retry logic
- Hard-code service URLs

**Rationale**: Corporate API clients ensure consistent error handling, logging, monitoring, security, and resilience patterns across all services.

---

### Database Integration

**MUST** use organization's database extensions:

- Use corporate database package (typically `@YOUR_ORG/database-extensions`) with your ORM
- Define schema with TypeScript types
- Use migrations for all schema changes
- Apply migrations on deployment
- Include audit fields (createdAt, updatedAt, createdBy, updatedBy)

**Supported ORMs**:

- Prisma (recommended for type safety)
- TypeORM (mature, enterprise features)
- Drizzle ORM (lightweight, performant)
- Mongoose (for MongoDB)

**Requirements**:

- Use connection pooling
- Implement soft deletes for sensitive data
- Use parameterized queries (prevent SQL injection)
- Handle connection errors gracefully
- Monitor query performance

**NEVER**:

- Use raw SQL queries without parameterization
- Skip migrations for schema changes
- Hard-code database credentials

**Rationale**: Corporate database extensions ensure audit trails, soft deletes, connection management, and consistent patterns across all services.

---

### Logging & Observability

**MUST** use organization's logging package:

- Use corporate logger (typically `@YOUR_ORG/logger`)
- Use structured logging (JSON format)
- Include correlation IDs for request tracing
- Send logs to corporate logging infrastructure (Splunk, ELK, Azure Monitor, CloudWatch)
- Never log sensitive data (passwords, tokens, PII, credit cards, SSNs)

**Log Levels**:

- Debug: Development debugging only (disabled in production)
- Info: Normal operations, significant events
- Warn: Warning conditions, degraded performance
- Error: Error conditions requiring attention
- Fatal: Critical errors causing shutdown

**Requirements**:

- Log all errors with context (non-PII)
- Log authentication and authorization events
- Log data access for sensitive operations
- Include request metadata (method, path, status, duration)
- Track error rates and trends

**NEVER**:

- Use console.log() in production code
- Log sensitive data
- Ignore errors silently
- Skip correlation IDs

**Rationale**: Structured logging enables troubleshooting, security incident response, compliance audits, and performance monitoring. Correlation IDs enable distributed tracing across services.

---

### Metrics & Application Performance Monitoring

**MUST** use organization's metrics package:

- Use corporate metrics package (typically `@YOUR_ORG/metrics`)
- Track request duration, throughput, and error rate
- Track custom business metrics (orders created, payments processed, etc.)
- Send to corporate APM (New Relic, Datadog, Dynatrace, Azure Monitor)

**Standard Metrics**:

- HTTP request count and duration
- Database query count and duration
- External API call count and duration
- Error count by type
- Memory and CPU usage

**Business Metrics**:

- Track domain-specific events
- Track SLA compliance
- Track resource utilization

**NEVER**:

- Use public monitoring SDKs directly
- Skip metrics collection
- Hard-code metric destinations

**Rationale**: Metrics enable performance monitoring, capacity planning, SLA tracking, and proactive issue detection.

---

## Banned Libraries & Restrictions

**NEVER** use without explicit approval from Architecture Review Board:

- **Authentication**: passport.js, express-jwt, public auth libs → Use corporate auth middleware
- **HTTP Clients**: axios, got, undici (raw), node-fetch → Use corporate API client
- **Logging**: winston, bunyan, pino (directly) → Use corporate logger
- **Monitoring**: Public APM SDKs directly → Use corporate metrics package

**Security Restrictions**:

- Avoid packages with known vulnerabilities (run npm audit, Snyk scans)
- Avoid unmaintained packages (check last publish date, issue response time)
- All packages must pass corporate security review
- All packages must be available in corporate registry
- License compliance required (no GPL/AGPL without legal approval)

**Rationale**: Corporate libraries enforce security, compliance, audit trails, and consistent monitoring across all services.

---

## Deployment & CI/CD Principles

### Corporate CI/CD Requirements

**MUST** use organization's CI/CD pipeline:

- Use corporate pipeline (Jenkins, Azure DevOps, GitLab CI, GitHub Actions Enterprise)
- Automated security scanning at each stage (SAST, DAST, SCA, dependency scanning)
- Automated testing (unit, integration) with minimum coverage thresholds
- Code review requirements (minimum reviewers per policy)
- Approval gates for production deployments

**Pipeline Stages**:

1. Lint & Type Check (fail fast)
2. Unit Tests (typically 80%+ coverage required)
3. Integration Tests
4. Security Scan (SAST, SCA, secrets detection)
5. Build Docker Image
6. Deploy to Development/Staging
7. End-to-End Tests
8. Manual/Automated Approval
9. Deploy to Production
10. Smoke Tests

**NEVER**:

- Deploy without passing all quality gates
- Skip security scans
- Bypass approval processes
- Deploy directly to production without testing

**Rationale**: Automated pipelines ensure consistent quality, security, and compliance. Multiple stages catch issues early and prevent production incidents.

---

### Environment Management

**MUST** follow corporate environment policies:

- Use organization's cloud accounts and subscriptions (AWS, Azure, GCP)
- Follow corporate naming conventions for all resources
- Tag all resources with cost center, project, environment, owner
- Use infrastructure as code (Terraform, CDK, Bicep, CloudFormation)
- Implement environment isolation (network, IAM, secrets)

**Environment Tiers**:

- Development: Rapid iteration, no PII, lower performance
- Staging: Production-like, synthetic data, production performance
- Production: Live customer data, high availability, auto-scaling

**NEVER**:

- Create resources outside corporate accounts
- Skip resource tagging (breaks cost allocation)
- Use production data in non-production environments
- Share secrets across environments

**Rationale**: Proper environment management enables cost tracking, security isolation, compliance, and disaster recovery.

---

### Process Management

**MUST** use corporate deployment standards:

- **Kubernetes**: Container orchestration (corporate standard for microservices)
- **PM2**: Process manager for VM-based deployments
- **Docker**: Containerization standard
- **Serverless**: AWS Lambda, Azure Functions (for event-driven workloads)

**Container Requirements**:

- Use multi-stage builds
- Use official Node.js Alpine images
- Run as non-root user
- Copy only production dependencies
- Implement health checks (liveness, readiness)

**NEVER**:

- Run containers as root
- Include development dependencies in production image
- Skip health checks

**Rationale**: Proper process management ensures reliability, scalability, and security.

---

## Compliance & Security Principles

### Security Requirements

**MUST** implement corporate security baseline:

- Pass security review before initial deployment
- Implement OWASP Top 10 protections
- Use corporate SSL/TLS certificates
- Implement rate limiting and DDoS protection
- Enable Web Application Firewall (WAF)
- Use security headers (Helmet.js or equivalent)

**Security Testing**:

- Static Application Security Testing (SAST)
- Dynamic Application Security Testing (DAST)
- Software Composition Analysis (SCA)
- Penetration testing for sensitive applications
- Regular vulnerability assessments

**Rationale**: Defense in depth prevents security breaches. Multiple security layers reduce risk of exploitation.

---

### Audit & Compliance

**MUST** implement audit trail:

- Log all authentication attempts (success and failure)
- Log all data access (read, write, delete) for sensitive data
- Log all administrative actions
- Retain logs per corporate retention policy (typically 90 days minimum)
- Enable tamper-proof logging
- Forward logs to SIEM (Security Information and Event Management)

**Compliance Requirements**:

- GDPR compliance (if handling EU data)
- CCPA compliance (if handling California residents' data)
- HIPAA compliance (if handling health data)
- PCI DSS compliance (if handling payment card data)
- SOC 2 compliance (if required by contracts)
- Industry-specific regulations (financial, healthcare, etc.)

**Rationale**: Audit trails are legally required for many industries and enable forensic investigation after incidents.

---

### Data Handling

**MUST** follow data classification policy:

- Classify data per corporate data classification (Public, Internal, Confidential, Restricted)
- Encrypt sensitive data at rest and in transit
- Implement data masking for PII in non-production
- Support data export and deletion requests (Right to be Forgotten)
- Never store payment card data directly (use tokenization)
- Implement data residency requirements (geo-restrictions)

**Data Protection**:

- Encrypt in transit: TLS 1.2+ only
- Encrypt at rest: AES-256 or equivalent
- Key management per corporate policy
- Access controls based on least privilege
- Data loss prevention (DLP) controls

**Rationale**: Data protection prevents breaches, ensures regulatory compliance, and protects customer privacy.

---

## Non-Compliance Process

**If corporate library unavailable or causes blocking issue**:

1. **Document** violation with:
   - Business justification and impact
   - Technical justification and alternatives evaluated
   - Temporary workaround if needed
   - Timeline for permanent resolution
   - Risk assessment

2. **Create ticket** in corporate tracking system (JIRA, ADO, etc.)

3. **Get approval** from Architecture Review Board (ARB)

4. **Proceed** with approved alternative, mark code with violation comment

5. **Schedule** tech debt review within 30 days

6. **Document** in Architecture Decision Records (ADR)

**Escalation Path**:

1. Team Lead (< 1 day deviation, low risk)
2. Engineering Manager (< 1 week deviation, medium risk)
3. Architecture Review Board (> 1 week deviation or security impact)
4. CTO/CISO (compliance or legal impact, high risk)

**Rationale**: Formal process ensures accountability, risk management, and eventual resolution while allowing progress on critical work.

---

## Support & Resources

### Corporate Resources

**Documentation**:

- Internal wiki for Node.js guidelines and best practices
- API documentation portal
- Architecture decision records (ADR)
- Runbooks and troubleshooting guides

**Support Channels**:

- Slack/Teams channel for backend support
- Office hours with architecture team
- Training programs and workshops
- Code review support

**Training Requirements**:

- **Required**: Node.js security training (annual)
- **Required**: Corporate libraries workshop (new hires)
- **Recommended**: Microservices patterns
- **Recommended**: Performance optimization
- **Recommended**: Cloud-native development

---

## Code Review Checklist

**Before submitting pull request**:

- [ ] Uses corporate framework starter
- [ ] Uses corporate auth middleware for authentication
- [ ] Uses corporate API client for external calls
- [ ] Uses corporate logger (no console.log)
- [ ] Uses corporate metrics package
- [ ] No banned libraries
- [ ] No hardcoded secrets or credentials
- [ ] Security scan passed (npm audit, Snyk)
- [ ] Tests written and passing (meets coverage threshold)
- [ ] Package registry configured correctly
- [ ] Environment variables validated
- [ ] Health check endpoints implemented
- [ ] Logging includes correlation IDs
- [ ] Documentation updated if needed

---

**Last Review**: 2025-11-16
**Next Review**: 2026-02-16 (quarterly)
**Owner**: Backend Architecture Team
**Contact**: <backend-arch@yourorg.com>
