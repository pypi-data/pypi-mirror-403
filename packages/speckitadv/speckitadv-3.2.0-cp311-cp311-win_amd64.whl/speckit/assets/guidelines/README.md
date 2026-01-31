# Corporate Guidelines System (Profile-Based Architecture)

**Version**: 3.0 (Profile-Based)
**Last Updated**: 2025-11-16
**Architecture**: Base + Profile Overrides

Guidelines for AI agents implementing Spec-Driven Development with modern technology stacks, supporting both **corporate/enterprise** and **personal/open-source** projects.

---

## 🆕 What's New in v3.0: Profile-Based Architecture

### Overview

Guidelines are now organized using a **base + profile override** architecture, eliminating duplication while supporting both corporate and personal projects:

- **Base Guidelines** (`base/`): Universal best practices (security, testing, architecture) - ~85-90% of content
- **Profile Overrides** (`profiles/`): Project-specific requirements (packages, registries, deployment) - ~10-15% of content

### Profiles

1. **Corporate Profile** (`profiles/corporate/`)
   - Internal/proprietary projects
   - Corporate package registries (@YOUR_ORG/*)
   - Enterprise authentication & monitoring
   - Audit & compliance requirements
   - Use when: Building internal tools, commercial products, regulated applications

2. **Personal Profile** (`profiles/personal/`)
   - Open-source/public projects
   - Public npm/PyPI/Maven packages
   - Free-tier services (Vercel, Supabase, Clerk)
   - Community recommendations
   - Use when: Personal projects, OSS libraries, learning projects, portfolio work

### How It Works

When implementing code:

1. **Profile is detected** from `memory/config.json` → `.guidelines-profile` file → package.json markers → filesystem markers
2. **Base guideline** is loaded (e.g., `base/reactjs-base.md`)
3. **Profile override** is loaded (e.g., `profiles/corporate/reactjs-overrides.md` or `profiles/personal/reactjs-overrides.md`)
4. **Composition**: Base principles + Profile specifics = Final guideline

**Priority**: Constitution > Profile Override > Base Guideline > Spec Kit Defaults

---

## Overview

This guidelines system provides technology-stack-specific best practices, security requirements, and architectural patterns for AI-driven software development. Guidelines are **principle-based** (defining WHAT and WHY, not HOW) to remain version-agnostic and adaptable across framework versions.

### Key Features

- ✅ **Modern Tech Stacks**: Latest LTS versions (Java 21, .NET 8, Python 3.12, Node.js 20/22, React 18+)
- ✅ **Cloud & On-Premise**: Deployment strategies for Azure, AWS, Kubernetes, self-hosted
- ✅ **Security First**: Authentication, secrets management, input validation, OWASP compliance
- ✅ **Observability**: OpenTelemetry, distributed tracing, metrics, structured logging
- ✅ **Performance**: Caching, connection pooling, async patterns, performance budgets
- ✅ **Compliance**: GDPR, WCAG 2.1 AA accessibility, audit logging, data protection
- ✅ **Framework-Specific**: Auto-detects Next.js, FastAPI, Spring Boot, NestJS, etc.
- ✅ **Monorepo Support**: Workspace detection, per-package guidelines

---

## Hierarchy

Priority order when making decisions:

1. **Constitution** (`/memory/constitution.md`) - **HIGHEST PRIORITY**
2. **Profile Override** (`profiles/corporate/` or `profiles/personal/`) - **HIGH PRIORITY**
3. **Base Guideline** (`base/`) - **MEDIUM PRIORITY**
4. **Spec Kit Defaults** - **LOWEST PRIORITY**

**Rule**: Constitution always wins. Profile overrides extend/override base guidelines. If constitution says "MUST use PostgreSQL", that overrides all guidelines.

---

## File Structure

```text
.guidelines/
├── README.md                          # This file - system documentation
│
├── base/                              # Universal best practices (shared across all projects)
│   ├── prompt-base.md                 # AI agent behavior guidelines (Claude Code derived)
│   ├── reactjs-base.md                # React security, testing, architecture
│   ├── nodejs-base.md                 # Node.js patterns, performance
│   ├── java-base.md                   # Java standards, SOLID principles
│   ├── python-base.md                 # Python best practices, PEPs
│   └── dotnet-base.md                 # .NET conventions, async patterns
│
├── profiles/                          # Project-type specific overrides
│   ├── corporate/                     # Corporate/Enterprise projects
│   │   ├── profile.json               # Profile metadata
│   │   ├── reactjs-overrides.md       # Corporate packages, registries
│   │   ├── nodejs-overrides.md        # Internal npm registry, auth
│   │   ├── java-overrides.md          # Corporate Maven artifacts
│   │   ├── python-overrides.md        # Internal PyPI, compliance
│   │   └── dotnet-overrides.md        # NuGet feeds, AD integration
│   │
│   └── personal/                      # Personal/Open-Source projects
│       ├── profile.json               # Profile metadata
│       ├── reactjs-overrides.md       # Public npm, Vercel, Supabase
│       ├── nodejs-overrides.md        # Free hosting, OSS tools
│       ├── java-overrides.md          # Maven Central, GitHub Actions
│       ├── python-overrides.md        # PyPI, Render, Railway
│       └── dotnet-overrides.md        # NuGet.org, Azure free tier
```

### Configuration

Profile selection is configured in `memory/config.json`:

```json
{
  "project": {
    "type": "personal",                 // or "corporate"
    "guidelineProfile": "personal"      // or "corporate"
  }
}
```

---

## Technology Stacks

### Supported Stacks (v2.0)

| Stack | Version | Frameworks | Status |
| ------- | --------- | ------------ | -------- |
| **React** | 18+ | Next.js 14+, Vite 5+, Remix | ✅ Active |
| **Java** | 21 LTS | Spring Boot 3.2+, Quarkus, Micronaut | ✅ Active |
| **.NET** | 8 LTS | ASP.NET Core, Blazor, gRPC | ✅ Active |
| **Node.js** | 20/22 LTS | Express 5, Fastify 4, NestJS 10 | ✅ Active |
| **Python** | 3.11/3.12 | FastAPI, Django 5, Flask 3 | ✅ Active |
| **Go** | 1.21+ | Gin, Echo, Fiber | 🚧 Planned |
| **Rust** | Latest | Actix, Rocket, Axum | 🚧 Planned |

### Framework Detection

The system automatically detects specific frameworks within each stack:

**React Ecosystem**:

- Next.js (detects `next.config.js`, App Router vs Pages Router)
- Vite (detects `vite.config.ts`)
- Remix (detects `remix.config.js`)

**Python Ecosystem**:

- FastAPI (detects `fastapi`, `uvicorn` dependencies)
- Django (detects `manage.py`, `INSTALLED_APPS`)
- Flask (detects `Flask(__name__)` patterns)

**Node.js Ecosystem**:

- Express (detects `express` dependency)
- Fastify (detects `fastify` dependency)
- NestJS (detects `nest-cli.json`, `@nestjs/core`)

**Java Ecosystem**:

- Spring Boot (detects `spring-boot-starter`)
- Quarkus (detects `quarkus-` dependencies)
- Micronaut (detects `micronaut-` dependencies)

**.NET Ecosystem**:

- ASP.NET Core (detects `Microsoft.AspNetCore.App`)
- Blazor (detects WebAssembly components)
- .NET MAUI (detects `Microsoft.Maui`)

---

## Stack Detection

AI agents detect the tech stack from standard project markers:

| Stack | Detection Markers |
|-------|-------------------|
| **React** | `package.json` with `react`, `next.config.js`, `vite.config.ts` |
| **Node.js** | `package.json` with `express`/`fastify`/`koa` |
| **Python** | `requirements.txt`, `pyproject.toml`, `manage.py` |
| **Java** | `pom.xml`, `build.gradle`, `*.java` files |
| **.NET** | `*.csproj`, `*.sln`, `*.cs` files |

For **multi-stack projects** (e.g., React + Java), load ALL applicable guidelines and apply contextually by component.

---

## Guideline Structure

### Principle-Based Format

**Philosophy**: Guidelines define **WHAT** and **WHY**, not **HOW**.

AI agents adapt principles to the target language/framework version, preventing:

- ❌ Build errors from outdated syntax
- ❌ Version incompatibilities (React 16 vs 18, .NET 6 vs 8)
- ❌ Stale code examples that don't match project setup

**Format**:

```markdown
### Category

**MUST** use: `@YOUR_ORG/package-name` package
**Requirements**:
- Requirement stated as principle (no code)
- Another principle-based requirement

**Features**: Auto-included features, benefits

**NEVER**:
- Prohibited action or library
```

### Requirement Keywords (RFC 2119 Style)

- **MUST**: Mandatory requirement (non-compliance requires documentation)
- **MUST NOT** / **NEVER**: Prohibited (security, compliance, or architectural reasons)
- **SHOULD**: Recommended (deviation acceptable with justification)
- **SHOULD NOT**: Not recommended (deviation acceptable with justification)
- **MAY**: Optional (discretionary)

---

## Version Management

### Guideline Versioning

Each guideline file includes version metadata:

```markdown
**Version**: 2.0
**Last Updated**: 2025-01-15
```

Configuration files include:

```json
{
  "version": "2.0",
  "last_updated": "2025-01-15"
}
```

### Technology Version Support

Guidelines specify **target versions**:

| Stack | Target Version | LTS Until | Next LTS |
| ------- | --------------- | ----------- | ---------- |
| Java | 21 LTS | Sep 2028 | Sep 2025 (Java 23 LTS) |
| .NET | 8 LTS | Nov 2026 | Nov 2025 (.NET 10 LTS) |
| Node.js | 20 LTS | Apr 2026 | Oct 2024 (Node.js 22 LTS) |
| Python | 3.12 | Oct 2028 | Oct 2025 (Python 3.13) |
| React | 18.2+ | Ongoing | 2025 (React 19) |

---

## Customization

### Replacing Placeholders

**Find and replace** across all `*-guidelines.md` files:

| Placeholder | Replace With |
| ------------- | -------------- |
| `@YOUR_ORG` | Your organization's package scope (e.g., `@acmecorp`) |
| `YOUR_ORG` | Your organization name (e.g., `acmecorp`) |
| `YOUR_DOMAIN` | Your organization domain (e.g., `acmecorp.com`) |

### Adding New Stacks

1. Create `base/{stack}-base.md` following principle-based format
2. Create `profiles/corporate/{stack}-overrides.md` for corporate requirements
3. Create `profiles/personal/{stack}-overrides.md` for personal project recommendations
4. Update this README with stack information

---

## Usage for AI Agents

### Loading Guidelines

**Steps**:

1. **Load Constitution** (if exists): `memory/constitution.md` - highest priority
2. **Detect Tech Stack**: From `package.json`, `requirements.txt`, `pom.xml`, etc.
3. **Detect Profile**: From `memory/config.json` → `.guidelines-profile` → default `personal`
4. **Load Base**: `.guidelines/base/{stack}-base.md`
5. **Load Override**: `.guidelines/profiles/{profile}/{stack}-overrides.md`
6. **Apply**: Constitution > Profile Override > Base > Defaults

### Principle Application

**When analyzing code**:

1. ✅ **Extract principles** from guidelines (MUST, SHOULD, NEVER)
2. ✅ **Adapt to project version** (React 18 vs 19, Java 17 vs 21)
3. ✅ **Apply contextually** (cloud vs on-premise, dev vs prod)
4. ❌ **Don't copy code examples verbatim** (guidelines don't include them)
5. ❌ **Don't apply outdated patterns** (adapt to target version)

**Example Adaptation**:

```text
Guideline Principle:
"MUST use async/await for all I/O operations"

✅ Java 21 (Virtual Threads):
Use virtual threads for high-concurrency I/O

✅ Python 3.11 (AsyncIO):
Use async/await with asyncio for non-blocking I/O

✅ Node.js 20 (Native Async):
Use async/await with proper error handling
```

### Non-Compliance Handling

When a guideline cannot be followed:

1. **Document** violation in `.guidelines-todo.md`:

```markdown
# Guideline Violations

## Node.js: Cannot use corporate HTTP client

**Guideline**: MUST use @YOUR_ORG/api-client
**Actual**: Using axios directly
**Reason**: Corporate package not compatible with Node.js 22
**Ticket**: TECH-1234
**Target Resolution**: Sprint 24
**Workaround**: Wrapped axios with retry logic and logging
```

1. **Mark in code** with tracking comment:

```typescript
// GUIDELINE-VIOLATION: Ticket #TECH-1234
// Using axios directly until @YOUR_ORG/api-client supports Node 22
import axios from 'axios';
```

1. **Create ticket** for resolution (target: next sprint)
1. **Schedule review** within 30 days

---

## Constitution vs Guidelines

### Constitution (`/memory/constitution.md`)

- **Purpose**: Project-specific principles and architectural decisions
- **Priority**: HIGHEST (overrides all guidelines)
- **Change Process**: Requires team vote or architect approval
- **Examples**:
  - "MUST use PostgreSQL for all databases"
  - "MUST use event-driven architecture for service communication"
  - "MUST support offline-first mobile experience"

### Corporate Guidelines (This Directory)

- **Purpose**: Organization-wide technology standards
- **Priority**: MEDIUM (overrides spec kit defaults)
- **Change Process**: Updated as standards evolve
- **Examples**:
  - "MUST use corporate authentication library"
  - "MUST log to corporate Elasticsearch cluster"
  - "SHOULD use corporate UI component library"

### Spec Kit Defaults

- **Purpose**: General best practices and fallback guidance
- **Priority**: LOWEST
- **Change Process**: Updated with spec kit releases
- **Examples**:
  - "SHOULD write unit tests for business logic"
  - "SHOULD use semantic versioning"
  - "SHOULD document public APIs"

---

## Best Practices

### For Teams

1. **Review Guidelines Quarterly**: Update for new LTS versions, security patches
2. **Customize Thoughtfully**: Add organization-specific requirements in moderation
3. **Document Exceptions**: Use `.guidelines-todo.md` for tracking deviations
4. **Share Learnings**: Feed real-world issues back to guideline improvements
5. **Version Lock**: Reference specific guideline version in project docs

### For AI Agents

1. **Load Once, Cache**: Parse guidelines at start, cache decisions per file/directory
2. **Respect Hierarchy**: Constitution > Guidelines > Defaults
3. **Be Version-Aware**: Detect project versions, adapt syntax accordingly
4. **Handle Conflicts**: Use precedence rules, document ambiguous cases
5. **Stay Current**: Check for guideline updates, flag outdated patterns

### For Developers

1. **Read Relevant Guidelines**: Familiarize yourself with applicable stack guidelines
2. **Question Thoughtfully**: Guidelines are principles, not absolute rules
3. **Propose Improvements**: Submit PRs for guideline enhancements
4. **Track Violations**: Use `.guidelines-todo.md` for transparency
5. **Educate Team**: Share guideline updates during tech talks

---

## Advanced Features

### Framework-Specific Guidance

AI agents adapt guidelines based on detected frameworks:

- **Next.js** (`next.config.js`): Use Server Components by default
- **Django** (`manage.py`): Use Django ORM with migrations
- **Spring Boot** (`spring-boot-starter`): Use dependency injection
- **FastAPI** (`fastapi` in deps): Use async patterns

---

## Migration Guide

### Upgrading from v1.0 to v2.0

**Major Changes**:

1. **Language Versions Updated**:
   - Java: 17 → 21 LTS
   - .NET: 6 → 8 LTS
   - Python: 3.10 → 3.12
   - Node.js: 18 → 20/22 LTS
   - React: 17 → 18+

2. **New Framework Support**:
   - Next.js 14+ App Router
   - FastAPI async patterns
   - Spring Boot 3.2+ native images
   - .NET 8 Blazor enhancements

3. **Enhanced Security**:
   - Secrets management expanded
   - mTLS support documented
   - Security headers mandated
   - OWASP Top 10 coverage

4. **Cloud-Native Focus**:
   - Azure/AWS deployment patterns
   - Kubernetes best practices
   - Observability with OpenTelemetry
   - Service mesh integration

**Migration Steps**:

1. **Review Dependencies**: Update to supported LTS versions
2. **Check Deprecations**: Remove banned libraries (CRA, moment.js, etc.)
3. **Update Patterns**: Adopt async patterns, server components
4. **Test Thoroughly**: Run full test suite after guideline updates
5. **Document Changes**: Update project docs with new patterns

---

## Troubleshooting

### Common Issues

**Issue**: AI applies wrong guidelines to file
**Solution**: Ensure correct tech stack markers exist (package.json, requirements.txt, etc.)

**Issue**: Guidelines conflict with constitution
**Solution**: Constitution always wins, document in `.guidelines-todo.md`

**Issue**: Corporate package not available
**Solution**: Follow non-compliance process, use alternative, create ticket

**Issue**: Wrong profile applied
**Solution**: Set `project.guidelineProfile` in `memory/config.json` or create `.guidelines-profile` file

---

## Contributing

### Proposing Guideline Changes

1. **Fork Repository**: Create feature branch (`feature/improve-react-security`)
2. **Make Changes**: Update guidelines with clear rationale
3. **Test Impact**: Validate against sample projects
4. **Submit PR**: Include justification, examples, migration notes
5. **Review Process**: Tech leads review, approve, merge

### Guideline Quality Checklist

- [ ] Principle-based (WHAT/WHY, not HOW)
- [ ] Version-agnostic (works across minor versions)
- [ ] Security-focused (OWASP, input validation, secrets)
- [ ] Cloud + on-premise coverage
- [ ] RFC 2119 keywords (MUST, SHOULD, MAY)
- [ ] Rationale provided for requirements
- [ ] Examples use placeholders (@YOUR_ORG)
- [ ] Non-compliance process documented

---

## References

### External Standards

- **OWASP Top 10**: <https://owasp.org/www-project-top-ten/>
- **WCAG 2.1**: <https://www.w3.org/WAI/WCAG21/quickref/>
- **GDPR**: <https://gdpr.eu/>
- **RFC 2119** (Requirement Levels): <https://www.rfc-editor.org/rfc/rfc2119>
- **OpenTelemetry**: <https://opentelemetry.io/>
- **12-Factor App**: <https://12factor.net/>

### Framework Documentation

- **React**: <https://react.dev/>
- **Next.js**: <https://nextjs.org/docs>
- **Spring Boot**: <https://spring.io/projects/spring-boot>
- **FastAPI**: <https://fastapi.tiangolo.com/>
- **.NET**: <https://learn.microsoft.com/en-us/dotnet/>

---

## Changelog

### Version 2.0 (2025-01-15)

**Added**:

- ✨ Next.js 14+ App Router support
- ✨ React Server Components guidance
- ✨ Java 21 LTS with virtual threads
- ✨ Python 3.12 with performance improvements
- ✨ .NET 8 LTS features
- ✨ Node.js 20/22 LTS support
- ✨ Framework-specific detection (Next.js, FastAPI, Spring Boot)
- ✨ Monorepo support (Nx, Turborepo, pnpm workspaces)
- ✨ Cloud-native deployment patterns (Azure, AWS, Kubernetes)
- ✨ OpenTelemetry distributed tracing
- ✨ Version detection system

**Changed**:

- 🔄 All guidelines updated to latest LTS versions
- 🔄 Enhanced security sections (secrets, mTLS, headers)
- 🔄 Improved observability guidance (metrics, logging, tracing)
- 🔄 Expanded performance optimization sections
- 🔄 Updated testing frameworks (Vitest, Playwright, Testcontainers)

**Deprecated**:

- ⚠️ Create React App (unmaintained)
- ⚠️ Log4j 1.x (security vulnerabilities)
- ⚠️ moment.js (discontinued, use date-fns/dayjs)

**Removed**:

- ❌ Code examples (principle-based approach)
- ❌ Version-specific syntax (adaptable to any version)

### Version 1.0 (2024-01-01)

- 🎉 Initial release
- Basic guidelines for React, Java, .NET, Node.js, Python

---

## License

Copyright © 2025 Your Organization. All rights reserved.

**Usage**: Internal use only. Do not distribute outside organization without approval.

---

## Support

**Questions?** Contact the Architecture Team:

- **Email**: <architecture@yourorg.com>
- **Slack**: #guidelines-support
- **Wiki**: <https://wiki.yourorg.com/guidelines>

**Issues?** File a ticket:

- **Jira Project**: GUIDELINES
- **GitHub Issues**: (if applicable)
