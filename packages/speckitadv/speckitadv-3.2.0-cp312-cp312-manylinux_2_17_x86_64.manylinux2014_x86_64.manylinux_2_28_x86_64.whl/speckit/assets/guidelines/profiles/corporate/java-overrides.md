# Java Corporate Profile Overrides

**Profile**: Corporate
**Stack**: Java
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only corporate-specific overrides. Base guidelines are inherited from `base/java-base.md`.
> **Philosophy**: These overrides define WHAT corporate Java projects require and WHY, not HOW to implement them.

---

## Scaffolding Principles

**MUST** use corporate-approved scaffolding:

- Use organization's Spring Boot starters or Quarkus templates
- Scaffolding includes pre-configured security, logging, monitoring, compliance
- Choose architecture template (REST API, microservice, batch job, messaging)

**Rationale**: Corporate scaffolding ensures security baselines, compliance, and observability from day one.

---

## Package Registry Principles

**MUST** use corporate artifact registry exclusively:

- Configure Maven/Gradle to use corporate registry (Artifactory, Nexus, Azure Artifacts)
- All dependencies resolved through corporate registry only
- Use authentication from environment variables or settings files

**Rationale**: Corporate registries provide security scanning, license compliance, and audit trails.

---

## Mandatory Corporate Libraries

**MUST** use organization's libraries:

- **Framework Starter**: Corporate Spring Boot starter or Quarkus extensions
- **Authentication**: Corporate auth library for OAuth 2.0, JWT, SAML
- **API Client**: Corporate RestTemplate/WebClient wrapper with resilience patterns
- **Logging**: Corporate logging framework (SLF4J + corporate appenders)
- **Metrics**: Corporate metrics library for APM integration

**Rationale**: Corporate libraries ensure consistent security, logging, monitoring, and compliance across all services.

---

## Deployment & CI/CD Principles

**MUST** use organization's pipeline:

- Corporate CI/CD (Jenkins, Azure DevOps, GitLab)
- Automated security scanning (SAST, SCA)
- Minimum test coverage thresholds (typically 80%+)
- Code review requirements
- Approval gates for production

**Rationale**: Automated pipelines ensure consistent quality and security.

---

## Compliance & Security Principles

**MUST** implement:

- Pass corporate security review
- OWASP Top 10 protections
- Corporate SSL/TLS certificates
- Audit logging for sensitive operations
- Data encryption at rest and in transit

**Rationale**: Security and compliance are non-negotiable for corporate applications.

---

**Last Review**: 2025-11-16
**Owner**: Java Architecture Team
**Contact**: <java-arch@yourorg.com>
