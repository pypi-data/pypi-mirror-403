# React Base Guidelines

**Tech Stack**: React 18+, TypeScript 5+, Next.js 14+ / Vite 5+, Frontend Web Applications, SPAs, SSR
**Auto-detected from**: `package.json` with `"react"` dependency
**Version**: 3.0 (Profile-Based Architecture - Principle-Based)
**Last Updated**: 2025-11-16

> **Philosophy**: These guidelines define WHAT and WHY, not HOW. They remain version-agnostic and adaptable across framework versions.

---

## Target Platform

**MUST**:

- Use React 18+ (concurrent features, automatic batching, Suspense)
- Use TypeScript 5+ for all new projects
- Use modern build tools: Next.js 14+ (full-stack) or Vite 5+ (SPA)
- Target modern browsers (ES2020+, no IE11 support)

**Rationale**: React 18+ provides concurrent rendering, automatic batching, and improved Suspense. TypeScript ensures type safety, better tooling, and maintainability. Modern build tools provide optimal developer experience and production performance.

---

## Framework Selection

**Principle**: Choose framework based on project requirements, rendering strategy, and deployment target

**Options**:

- **Next.js 14+**: Full-stack React framework, SSR/SSG/ISR, API routes, file-based routing, React Server Components
- **Vite 5+**: Ultra-fast dev server, SPA, client-side routing, optimal for pure frontend apps
- **Remix**: Web fundamentals focused, progressive enhancement, nested routing
- **Astro**: Content-focused sites, partial hydration, multi-framework support

**NEVER**:

- Use deprecated Create React App (CRA) - unmaintained since 2022

**Rationale**: Different frameworks excel at different use cases. Next.js for full-stack with SEO needs, Vite for pure client-side apps, Remix for progressive enhancement, Astro for content-heavy sites.

---

## State Management Principles

**Principle**: Choose state management based on state type and complexity

**State Classification**:

- **Server state** (API data, cached responses) → TanStack Query (React Query)
- **Client state** (UI state, forms) → React Context + useReducer (simple) or Zustand (complex)
- **URL state** (filters, pagination, search) → URL search parameters
- **Form state** (user inputs, validation) → React Hook Form or Formik

**Options by Complexity**:

- **Simple**: React Context + useReducer (built-in, zero dependencies)
- **Medium**: Zustand (lightweight, minimal boilerplate, DevTools support)
- **Complex**: Redux Toolkit (predictable, time-travel debugging, extensive ecosystem)
- **Server state**: TanStack Query (handles caching, synchronization, background updates)

**NEVER**:

- Mix server and client state in same store
- Use legacy Redux without Redux Toolkit

**Rationale**: Separating state by type prevents unnecessary complexity. Server state requires different handling than client state (caching, revalidation, background updates).

---

## Routing Principles

**Next.js**:

- Use App Router (app/ directory) for new projects
- Use Server Components by default, 'use client' only when needed
- Leverage file-based routing, layouts, parallel routes, intercepting routes

**Vite/SPA**:

- Use React Router 6+ for client-side routing
- Use data loaders for route-level data fetching
- Implement error boundaries per route
- Consider TanStack Router for type-safe routing

**Rationale**: File-based routing reduces boilerplate and improves discoverability. Data loaders prevent waterfall requests.

---

## Styling Principles

**Principle**: Choose one styling approach and maintain consistency project-wide

**Options**:

- **Tailwind CSS**: Utility-first, rapid development, design system constraints (recommended for most projects)
- **CSS Modules**: Scoped CSS, zero runtime, works everywhere
- **CSS-in-JS**: styled-components, Emotion (runtime cost, use cautiously, avoid in Server Components)
- **Vanilla Extract**: Zero-runtime CSS-in-TS (type-safe, best of both worlds)
- **Sass/SCSS**: Traditional preprocessor (legacy projects)

**MUST**:

- Be consistent with one approach per project
- Use utility function for conditional classes
- Avoid mixing multiple styling approaches in same component

**NEVER**:

- Use inline styles for complex styling
- Use !important (refactor specificity instead)

**Rationale**: Consistency improves maintainability. Utility-first CSS reduces bundle size and enables design system constraints.

---

## Form Handling Principles

**MUST** validate inputs on both client and server

**Options**:

- **React Hook Form**: Performance-focused, minimal re-renders (recommended)
- **Formik**: Full-featured, more re-renders
- **Native HTML forms**: Next.js Server Actions (progressive enhancement)

**MUST**:

- Use schema validation libraries (Zod, Yup)
- Validate on client (UX) and server (security)
- Provide clear error messages
- Handle loading and error states

**Rationale**: Client validation improves UX, server validation ensures security. Schema validation provides type safety and reusable validation logic.

---

## Architecture Principles

### Project Structure

**MUST** organize by feature/domain rather than technical layer:

**Benefits**:

- Related code stays together
- Easy to locate functionality
- Clear module boundaries
- Scalable for large applications
- Supports code splitting by feature

**Rationale**: Domain-driven organization scales better than layered organization as applications grow.

### Separation of Concerns

**MUST**:

- Keep components focused on presentation
- Extract business logic to custom hooks
- Extract API calls to service files
- Use custom hooks for complex state logic
- Separate server and client code (Next.js App Router)

**Rationale**: Clear separation improves testability, reusability, and allows independent evolution of each concern.

### Component Organization

**MUST**:

- One component per file (except small, tightly coupled helpers)
- Co-locate tests, styles, types with components
- Use named exports for better refactoring support
- Keep components small and focused (< 200 lines ideal)

**Rationale**: Co-location improves discoverability and reduces navigation overhead.

### Server vs Client Components (Next.js App Router)

**MUST**:

- Use Server Components by default (no 'use client' directive)
- Use 'use client' only when needed:
  - useState, useEffect, browser event handlers
  - Browser APIs (localStorage, window, document)
  - Context providers
  - Third-party libraries requiring client features

**Rationale**: Server Components reduce bundle size, improve initial load performance, and enable direct database access.

---

## Security Principles

### XSS Prevention

**MUST**:

- Never use `dangerouslySetInnerHTML` unless absolutely necessary
- Sanitize HTML with DOMPurify if user HTML must be rendered
- Validate and escape all user inputs
- Use Content Security Policy (CSP) headers

**Rationale**: React escapes content by default, but dangerouslySetInnerHTML bypasses protection. CSP provides defense-in-depth.

### Environment Variables

**MUST**:

- Prefix public env vars with framework convention (NEXT_PUBLIC_, VITE_)
- Never expose secrets to client-side code
- Use .env.local for local development (gitignored)
- Validate environment variables at build/runtime

**NEVER**:

- Hardcode API keys or secrets in code
- Commit .env files to version control
- Expose server-side secrets to client code

**Rationale**: Environment variables enable configuration per environment. Validation prevents runtime failures from misconfiguration.

### Authentication & Authorization

**MUST**:

- Validate user session on every protected page/API route
- Use middleware for route protection (Next.js)
- Store tokens securely (httpOnly cookies, not localStorage)
- Implement CSRF protection for state-changing operations
- Use secure, sameSite cookies

**NEVER**:

- Store tokens in localStorage (vulnerable to XSS)
- Trust client-side authorization checks only
- Skip validation on "internal" routes

**Rationale**: httpOnly cookies prevent XSS token theft. Server-side validation is critical as client code can be manipulated.

### Content Security Policy

**MUST** implement CSP headers:

- Restrict script sources to prevent XSS
- Restrict style sources
- Restrict image and font sources
- Enable X-Content-Type-Options: nosniff
- Enable X-Frame-Options: DENY (or SAMEORIGIN)
- Configure Referrer-Policy

**Rationale**: CSP provides additional XSS protection layer. Defense in depth prevents single point of failure.

### Input Validation

**MUST**:

- Validate all user inputs with schema validation (Zod, Yup)
- Validate on both client (UX) and server (security)
- Sanitize inputs before rendering
- Use TypeScript for compile-time type safety

**Rationale**: Client validation can be bypassed. Server validation is security-critical. TypeScript catches type errors at compile time.

---

## TypeScript Principles

**MUST**:

- Use TypeScript for all new code
- Enable strict mode in tsconfig.json
- Enable noUncheckedIndexedAccess (prevent undefined access bugs)
- Define types/interfaces for all props, state, API responses
- Use type inference where possible (avoid over-annotation)

**NEVER**:

- Use `any` type (use `unknown` if type is truly unknown)
- Disable TypeScript checks with @ts-ignore (use @ts-expect-error with explanation)
- Use excessive type assertions (`as`) - fix type definitions instead

**Rationale**: Strict TypeScript configuration catches bugs at compile time, improves refactoring safety, and serves as documentation.

---

## Component Design Principles

**MUST**:

- Use functional components (no class components)
- Use hooks for state and side effects
- Define prop types with TypeScript interfaces
- Follow Single Responsibility Principle
- Keep components pure when possible

### Hooks Best Practices

**MUST**:

- Follow Rules of Hooks (only at top level, only in function components/hooks)
- Provide correct dependency arrays in useEffect, useMemo, useCallback
- Extract complex logic to custom hooks
- Use useCallback for functions passed to children (prevent re-renders)
- Use useMemo for expensive computations only

**NEVER**:

- Omit dependencies from dependency arrays
- Use useEffect for derived state (compute during render instead)
- Optimize prematurely (profile first)

**Rationale**: Correct dependency arrays prevent bugs. Custom hooks enable reuse and testing. Premature optimization adds complexity without benefit.

---

## Performance Principles

### Core Web Vitals

**MUST** meet Google's Core Web Vitals:

- **LCP (Largest Contentful Paint)**: < 2.5s
- **INP (Interaction to Next Paint)**: < 200ms
- **CLS (Cumulative Layout Shift)**: < 0.1

**Rationale**: Core Web Vitals impact SEO rankings and user experience. Poor performance increases bounce rates.

### Performance Budget

**SHOULD** set and enforce limits:

- Initial bundle size: < 500KB gzipped
- Total page weight: < 2MB
- Time to Interactive: < 5 seconds (3G network)

**Rationale**: Performance budgets prevent regressions. Users on slower networks are disproportionately affected by bundle size.

### Optimization Strategies

**SHOULD**:

- Use React.memo for expensive components (profile first)
- Use code splitting and lazy loading for heavy components
- Optimize images (WebP/AVIF, lazy load, responsive images)
- Use dynamic imports for conditional features
- Avoid premature optimization (measure first)

**MUST**:

- Lazy load images below the fold
- Provide width/height for images (prevent CLS)
- Use tree-shaking friendly imports
- Analyze bundle size regularly

**Rationale**: Code splitting reduces initial bundle. Image optimization is often the highest-impact performance improvement.

---

## Testing Principles

### Test Pyramid

**MUST** implement:

- **Unit Tests**: Test components, hooks, utilities (70% of tests)
- **Integration Tests**: Test user flows, API integration (20% of tests)
- **E2E Tests**: Test critical paths (10% of tests)

**Target**: 80%+ code coverage on critical paths

**Rationale**: Test pyramid balances speed, confidence, and maintenance cost.

### Testing Practices

**MUST**:

- Test behavior, not implementation
- Use React Testing Library (user-centric queries)
- Use semantic queries (getByRole, getByLabelText) over test IDs
- Mock external dependencies (API calls, browser APIs)
- Test accessibility in component tests

**SHOULD**:

- Use Vitest (faster) or Jest for unit tests
- Use Playwright or Cypress for E2E tests
- Implement visual regression testing (Chromatic, Percy)

**Rationale**: Testing behavior ensures tests survive refactoring. User-centric queries improve test resilience and accessibility.

---

## Build & Deployment Principles

### Build Optimization

**MUST**:

- Enable production optimizations (minification, tree shaking)
- Use Image Optimization (next/image or equivalents)
- Use Font Optimization
- Enable bundle analysis to identify large dependencies
- Configure chunk splitting for optimal caching

**Rationale**: Production optimizations reduce bundle size and improve load times. Bundle analysis prevents dependency bloat.

### Rendering Strategies

**Static Site Generation (SSG)** for:

- Marketing pages, blog posts, documentation
- Content that changes infrequently
- Maximum performance requirements

**Server-Side Rendering (SSR)** for:

- Personalized content, real-time data
- SEO-critical pages with dynamic content
- Pages requiring authentication

**Client-Side Rendering (CSR)** for:

- Highly interactive applications (dashboards, editors)
- Authenticated private pages
- Real-time collaborative features

**Rationale**: Different rendering strategies optimize for different use cases. SSG provides best performance, SSR provides fresh data, CSR provides rich interactivity.

### Deployment

**MUST**:

- Use containerization (Docker) for self-hosted deployments
- Implement health checks
- Use CDN for static assets
- Enable compression (gzip, brotli)
- Configure caching headers appropriately

**Rationale**: Containerization ensures consistency across environments. CDN and caching reduce server load and improve global performance.

---

## Accessibility Principles

**MUST**:

- Meet WCAG 2.1 Level AA compliance
- Use semantic HTML elements (button, nav, main, article, section)
- Provide alt text for all images
- Support keyboard navigation (tab, enter, escape, arrow keys)
- Provide focus indicators
- Use ARIA attributes when semantic HTML insufficient
- Test with screen readers (NVDA, JAWS, VoiceOver)

**SHOULD**:

- Use automated testing (axe DevTools, Lighthouse)
- Use eslint-plugin-jsx-a11y
- Test with keyboard only
- Test with screen reader + keyboard

**Rationale**: Accessibility is a legal requirement in many jurisdictions and improves UX for all users. Semantic HTML provides built-in accessibility.

---

## Observability Principles

### Error Monitoring

**SHOULD**:

- Integrate error tracking (Sentry, Bugsnag, Application Insights)
- Implement Error Boundaries for graceful degradation
- Log errors with context (non-PII)
- Track error rates and trends

**Rationale**: Error monitoring enables rapid issue detection and resolution. Error boundaries prevent entire app crashes.

### Performance Monitoring

**SHOULD**:

- Track Core Web Vitals
- Monitor bundle size changes
- Track API response times
- Use Real User Monitoring (RUM)
- Set up performance regression alerts

**Rationale**: Performance monitoring detects regressions before users complain. RUM provides real-world performance data.

### Analytics

**SHOULD**:

- Track user interactions and conversions
- Implement funnel analysis
- Respect user privacy (GDPR, CCPA compliance)
- Provide opt-out mechanisms

**Rationale**: Analytics inform product decisions. Privacy compliance is legally required and builds user trust.

---

## Internationalization Principles

**SHOULD** implement for multi-language support:

- Use i18n libraries (next-intl, react-i18next, Format.js)
- Store translations in separate files
- Use ICU message format for complex messages
- Handle RTL languages properly
- Format dates, numbers, currencies per locale

**Rationale**: Proper i18n expands market reach. ICU format handles plurals, gender, and complex grammar.

---

## Compliance & Governance Principles

### Data Protection

**MUST**:

- Implement cookie consent (GDPR, CCPA)
- Provide privacy policy and terms of service
- Support data deletion requests
- Minimize data collection
- Encrypt sensitive data

**Rationale**: Privacy regulations are legally binding. Data minimization reduces liability.

### Security Audits

**SHOULD**:

- Run npm audit regularly
- Use Snyk or Dependabot for dependency scanning
- Conduct code reviews with security focus
- Perform penetration testing for sensitive applications

**Rationale**: Regular audits prevent accumulation of vulnerabilities. Automated scanning catches known issues early.

---

## Dependency Management Principles

### Package Selection

**MUST** evaluate:

- Security (known vulnerabilities, audit history)
- Maintenance (last update, active maintainers, issue response time)
- License compatibility
- Bundle size impact
- TypeScript support
- Community adoption

**Rationale**: Dependencies become part of your codebase and security surface. Choose wisely to minimize maintenance burden.

### Updates

**SHOULD**:

- Run security audits regularly
- Update dependencies on schedule
- Test updates in non-production first
- Use lock files (package-lock.json, yarn.lock)
- Monitor for breaking changes

**Rationale**: Regular updates prevent accumulation of security vulnerabilities and reduce update difficulty.

---

## Recommended Library Categories

**Date/Time**: date-fns (tree-shakeable), dayjs (lightweight), Luxon
**Validation**: Zod (TypeScript-first), Yup, joi
**Icons**: lucide-react, react-icons, heroicons
**Utilities**: lodash-es (tree-shakeable), native JavaScript methods (preferred)

**NEVER**:

- moment.js (deprecated, large bundle)
- Full lodash (not tree-shakeable)
- jQuery (use native DOM or React patterns)

**Rationale**: Modern alternatives provide better performance and bundle size. Native JavaScript methods eliminate dependencies.

---

**Note**: These are principle-based guidelines defining WHAT to do and WHY. Implementation details (HOW) vary by framework version and project requirements. Refer to official documentation for current syntax and APIs.
