# Python Corporate Profile Overrides

**Profile**: Corporate
**Stack**: Python
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only corporate-specific overrides. Base guidelines are inherited from `base/python-base.md`.
> **Philosophy**: These overrides define WHAT corporate Python projects require and WHY, not HOW to implement them.

---

## Scaffolding Principles

**MUST** use corporate-approved scaffolding: Organization's FastAPI/Django templates with pre-configured security, logging, monitoring.

**Rationale**: Corporate scaffolding ensures compliance and observability from day one.

---

## Package Registry Principles

**MUST** use corporate PyPI registry exclusively (Artifactory, Nexus, Azure Artifacts). Configure pip/poetry to use corporate registry only.

**Rationale**: Corporate registries provide security scanning and license compliance.

---

## Mandatory Corporate Libraries

**MUST** use: Corporate auth library, API client wrapper, logging framework, metrics library.

**Rationale**: Consistent security, logging, and monitoring across all services.

---

## Deployment & CI/CD Principles

**MUST** use corporate CI/CD pipeline with automated security scanning and minimum test coverage thresholds.

**Rationale**: Automated pipelines ensure quality and security.

---

**Last Review**: 2025-11-16
**Owner**: Python Architecture Team
**Contact**: <python-arch@yourorg.com>
