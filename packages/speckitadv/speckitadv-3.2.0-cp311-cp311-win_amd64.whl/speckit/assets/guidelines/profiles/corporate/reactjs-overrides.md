# React Corporate Profile Overrides

**Profile**: Corporate
**Stack**: React
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only corporate-specific overrides. Base guidelines are inherited from `base/reactjs-base.md`.
> **Philosophy**: These overrides define WHAT corporate projects require and WHY, not HOW to implement them.

---

## Scaffolding Principles

**MUST** use corporate-approved scaffolding:

- Use organization's scaffolding tools (typically scoped packages like `@YOUR_ORG/create-react-app`)
- Choose template based on rendering strategy (Next.js App Router, Pages Router, Vite SPA, Remix, or microfrontend)
- Scaffolding includes pre-configured: security, authentication, logging, monitoring, accessibility, observability

**NEVER**:

- Use public scaffolding tools without security review
- Start from scratch without corporate starter templates

**Rationale**: Corporate scaffolding ensures security baselines, compliance requirements, and observability from day one. Prevents security gaps and reduces setup time.

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

### UI Component System

**MUST** use organization's UI component library:

- Use corporate component package (typically `@YOUR_ORG/ui-components`)
- Components include built-in accessibility (WCAG 2.1 Level AA minimum)
- Components follow corporate design system and brand guidelines
- TypeScript definitions included

**Benefits**:

- Consistent user experience across applications
- Built-in security (XSS prevention, input sanitization)
- Accessibility compliance out-of-the-box
- Internationalization support
- Reduced development time

**NEVER**:

- Use public UI libraries without approval (Material-UI, Ant Design, Chakra UI, etc.)
- Build custom UI components that duplicate corporate library functionality
- Bypass corporate design system

**Rationale**: Consistency ensures brand integrity, reduces training costs, and ensures compliance. Custom components often lack proper accessibility and security testing.

---

### Authentication & Authorization

**MUST** use organization's authentication client:

- Use corporate auth package (typically `@YOUR_ORG/auth-client`)
- Support corporate identity providers (Azure AD, Okta, corporate SSO)
- Implement OAuth 2.0, OpenID Connect, or SAML as per policy
- Support multi-factor authentication (MFA)
- Handle token refresh automatically

**Requirements**:

- Wrap application with authentication provider
- Protect routes based on authentication state
- Protect routes based on user roles and permissions
- Pass authentication tokens to API calls automatically
- Log authentication events for audit trail

**NEVER**:

- Store tokens in localStorage (XSS vulnerability)
- Implement custom authentication without security review
- Skip authorization checks on "internal" routes
- Use public authentication libraries without approval

**Rationale**: Authentication is security-critical. Corporate libraries ensure consistent security posture, compliance with identity policies, and integration with corporate identity systems.

---

### API Client & Data Fetching

**MUST** use organization's API client:

- Use corporate API client package (typically `@YOUR_ORG/api-client`)
- Automatic authentication token injection
- Built-in retry logic with exponential backoff
- Request/response interceptors for logging and monitoring
- Automatic error handling and reporting
- Request deduplication

**Requirements**:

- Use provided hooks for data fetching (GET requests)
- Use provided hooks for mutations (POST/PUT/DELETE)
- Never use raw fetch() or third-party HTTP clients directly
- Handle loading and error states appropriately

**Features**:

- Automatic token refresh on expiration
- Caching and invalidation strategies
- Optimistic updates support
- WebSocket support for real-time features
- Circuit breaker pattern for resilience

**NEVER**:

- Use raw fetch(), axios, or other HTTP clients directly
- Skip error handling
- Implement custom retry logic

**Rationale**: Corporate API clients ensure consistent error handling, logging, monitoring, security, and resilience patterns across all applications.

---

### Logging & Observability

**MUST** use organization's logging package:

- Use corporate logger (typically `@YOUR_ORG/logger`)
- Log user actions for audit trail (authentication, data access, critical operations)
- Include correlation IDs for request tracing
- Send logs to corporate logging infrastructure (Splunk, ELK, Azure Monitor)
- Never log sensitive data (passwords, tokens, PII, credit cards, SSNs)

**Log Levels**:

- Debug: Development debugging only
- Info: Normal operations, significant events
- Warn: Warning conditions, degraded performance
- Error: Error conditions requiring attention
- Fatal: Critical errors causing shutdown

**Requirements**:

- Implement Error Boundaries for graceful degradation
- Log all errors with context (non-PII)
- Track error rates and trends
- Send errors to corporate monitoring service (Sentry, Azure Monitor, AWS CloudWatch)

**NEVER**:

- Use console.log() in production code
- Log sensitive data
- Ignore errors silently

**Rationale**: Structured logging enables troubleshooting, security incident response, compliance audits, and performance monitoring. Correlation IDs enable distributed tracing.

---

### Analytics & User Tracking

**MUST** use organization's analytics package:

- Use corporate analytics (typically `@YOUR_ORG/analytics`)
- Track page views, user interactions, business events, conversions
- Comply with privacy regulations (GDPR, CCPA, HIPAA if applicable)
- Implement cookie consent management
- Never track PII without explicit consent and legal approval

**Requirements**:

- Track critical user journeys and funnels
- Implement performance monitoring
- Respect user privacy preferences
- Provide opt-out mechanisms
- Data retention per corporate policy

**NEVER**:

- Use public analytics without privacy review
- Track sensitive data without consent
- Skip cookie consent implementation

**Rationale**: Corporate analytics ensure privacy compliance, data governance, and integration with business intelligence systems.

---

## Banned Libraries & Restrictions

**NEVER** use without explicit approval from Architecture Review Board:

- **UI Libraries**: Public component libraries → Use corporate UI components
- **Authentication**: Public auth libraries → Use corporate auth client
- **API Clients**: axios, fetch wrappers, public clients → Use corporate API client
- **Logging**: console.log, custom loggers, public logging → Use corporate logger
- **Analytics**: Google Analytics, public analytics → Use corporate analytics

**Security Restrictions**:

- Avoid packages with known vulnerabilities (run npm audit, Snyk scans)
- Avoid unmaintained packages (check last publish date, issue response time)
- All packages must pass corporate security review
- All packages must be available in corporate registry
- License compliance required (no GPL/AGPL without legal approval)

**Rationale**: Corporate libraries enforce security, accessibility, compliance, brand consistency, and audit trails. Public libraries may have security vulnerabilities, licensing issues, or missing audit capabilities.

---

## Deployment & CI/CD Principles

### Corporate CI/CD Requirements

**MUST** use organization's CI/CD pipeline:

- Use corporate pipeline (Jenkins, Azure DevOps, GitLab CI, GitHub Actions Enterprise)
- Automated security scanning at each stage (SAST, DAST, dependency scanning)
- Automated testing (unit, integration, E2E) with minimum coverage thresholds
- Code review requirements (minimum reviewers per policy)
- Approval gates for production deployments

**Pipeline Stages**:

1. Lint & Type Check (fail fast)
2. Unit Tests (typically 80%+ coverage required)
3. Integration Tests
4. Security Scan (SAST, SCA, secrets detection)
5. Build & Package
6. Deploy to Development/Staging
7. End-to-End Tests
8. Manual/Automated Approval
9. Deploy to Production
10. Smoke Tests

**NEVER**:

- Deploy without passing all quality gates
- Skip security scans
- Bypass approval processes
- Deploy directly to production

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

- Development: Rapid iteration, no PII
- Staging: Production-like, synthetic data
- Production: Live customer data, high availability

**NEVER**:

- Create resources outside corporate accounts
- Skip resource tagging (breaks cost allocation)
- Use production data in non-production environments
- Share secrets across environments

**Rationale**: Proper environment management enables cost tracking, security isolation, compliance, and disaster recovery.

---

### Monitoring & Observability

**MUST** integrate with corporate monitoring:

- **APM**: Application Performance Monitoring per corporate standard
- **Logging**: Central logging system (Splunk, ELK, Azure Monitor, CloudWatch)
- **Error Tracking**: Corporate Sentry instance or equivalent
- **Alerts**: Integration with PagerDuty, OpsGenie, or corporate alerting
- **Metrics**: Track Core Web Vitals, API latency, error rates, business metrics

**Requirements**:

- Implement health check endpoints (liveness, readiness)
- Set up alerts for critical errors and performance degradation
- Monitor business KPIs and SLOs
- Enable distributed tracing for microservices
- Implement synthetic monitoring for critical paths

**Rationale**: Observability enables rapid incident detection, troubleshooting, capacity planning, and meeting SLAs.

---

## Compliance & Security Principles

### Security Requirements

**MUST** implement corporate security baseline:

- Pass security review before initial deployment
- Implement OWASP Top 10 protections
- Use corporate SSL/TLS certificates
- Implement rate limiting and DDoS protection
- Enable Web Application Firewall (WAF)
- Content Security Policy (CSP) headers
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)

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

- Internal wiki for React guidelines and best practices
- Component library documentation (Storybook or equivalent)
- API documentation portal
- Architecture decision records (ADR)

**Support Channels**:

- Slack/Teams channel for frontend support
- Office hours with architecture team
- Training programs and workshops
- Code review support

**Training Requirements**:

- **Required**: Security training (annual)
- **Required**: Corporate component library workshop (new hires)
- **Recommended**: Advanced React patterns
- **Recommended**: Performance optimization
- **Recommended**: Accessibility training

---

## Code Review Checklist

**Before submitting pull request**:

- [ ] Uses corporate UI components (no banned libraries)
- [ ] Uses corporate auth client for authentication
- [ ] Uses corporate API client for all HTTP requests
- [ ] Uses corporate logger (no console.log)
- [ ] No hardcoded secrets or credentials
- [ ] Security scan passed (npm audit, Snyk)
- [ ] Tests written and passing (meets coverage threshold)
- [ ] Accessibility tested (automated and manual)
- [ ] Performance budget met (bundle size, Core Web Vitals)
- [ ] Package registry configured correctly
- [ ] Environment variables validated
- [ ] Error boundaries implemented
- [ ] Logging includes correlation IDs
- [ ] Documentation updated if needed

---

**Last Review**: 2025-11-16
**Next Review**: 2026-02-16 (quarterly)
**Owner**: Frontend Architecture Team
**Contact**: <frontend-arch@yourorg.com>
