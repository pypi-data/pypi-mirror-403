# .NET Corporate Profile Overrides

**Profile**: Corporate
**Stack**: .NET
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only corporate-specific overrides. Base guidelines are inherited from `base/dotnet-base.md`.
> **Philosophy**: These overrides define WHAT corporate .NET projects require and WHY, not HOW to implement them.

---

## Scaffolding Principles

**MUST** use corporate-approved templates: Organization's dotnet templates with pre-configured security, logging, monitoring.

**Rationale**: Corporate templates ensure compliance and observability from day one.

---

## Package Registry Principles

**MUST** use corporate NuGet feed exclusively (Artifactory, Azure Artifacts, GitHub Packages). Configure NuGet.config with corporate registry.

**Rationale**: Corporate registries provide security scanning and license compliance.

---

## Mandatory Corporate Libraries

**MUST** use: Corporate auth library, HTTP client wrapper, logging framework, metrics library.

**Rationale**: Consistent security, logging, and monitoring across all services.

---

## Deployment & CI/CD Principles

**MUST** use corporate CI/CD pipeline with automated security scanning and minimum test coverage thresholds.

**Rationale**: Automated pipelines ensure quality and security.

---

**Last Review**: 2025-11-16
**Owner**: .NET Architecture Team
**Contact**: <dotnet-arch@yourorg.com>
