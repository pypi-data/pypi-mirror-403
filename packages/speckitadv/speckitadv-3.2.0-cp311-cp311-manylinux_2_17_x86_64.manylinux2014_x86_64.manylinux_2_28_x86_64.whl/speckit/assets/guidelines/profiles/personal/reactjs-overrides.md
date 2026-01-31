# React Personal/Public Profile Overrides

**Profile**: Personal/Public Open Source
**Stack**: React
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only personal/public project-specific overrides. Base guidelines are inherited from `base/reactjs-base.md`.
> **Philosophy**: These overrides define WHAT personal projects benefit from and WHY, not HOW to implement them. Prioritize developer experience, community packages, and cost-effective solutions.

---

## Scaffolding Principles

**RECOMMENDED** scaffolding approaches:

- **Vite + React**: Ultra-fast dev server, modern build tooling, excellent TypeScript support
- **Next.js**: Built-in routing, optimization, TypeScript support, choose App Router for new projects
- **Remix**: Web fundamentals focused, progressive enhancement, great for full-stack apps
- **Starter templates**: Use community templates for faster setup with pre-configured tooling

**Options by project type**:

- SPA with client-side routing → Vite + React Router
- Full-stack with SSR/SSG → Next.js
- Content-focused sites → Astro or Next.js
- Progressive enhancement → Remix

**NEVER**:

- Use deprecated Create React App (CRA) - unmaintained since 2022

**Rationale**: Modern scaffolding tools provide optimal developer experience, fast builds, and production-ready configurations out of the box.

---

## Package Registry Principles

**RECOMMENDED**:

- Use official npm registry (npmjs.org) as primary source
- Consider pnpm for faster installs and disk space efficiency
- Consider bun for ultra-fast package management
- Run security audits regularly to check for vulnerabilities

**Security practices**:

- Run `npm audit` regularly
- Use automated dependency updates (Dependabot, Renovate)
- Review package.json for unused dependencies
- Check package popularity and maintenance status before installing

**Rationale**: Public npm registry provides access to vast ecosystem. Modern package managers (pnpm, bun) improve performance and disk usage.

---

## Recommended Library Categories

### UI Components

**Principle**: Choose based on project needs and customization requirements

**Popular options**:

1. **shadcn/ui**: Copy-paste components, full customization control, no package dependency
2. **Radix UI**: Unstyled accessible primitives, bring your own styles
3. **Headless UI**: Unstyled components by Tailwind Labs, designed for Tailwind CSS
4. **MUI (Material-UI)**: Comprehensive component library, Material Design
5. **Chakra UI**: Component library with built-in theming, excellent accessibility
6. **Mantine**: 100+ customizable components, built-in dark mode

**Selection criteria**:

- Customization needs (copy-paste vs npm package)
- Design system requirements
- Accessibility built-in
- Bundle size impact
- Community support and documentation

**Rationale**: Different projects have different needs. Choose based on customization requirements, design constraints, and team preferences.

---

### Authentication

**Principle**: Choose based on ease of use, features needed, and budget

**Popular options**:

1. **Clerk**: Drop-in authentication, beautiful pre-built UI, generous free tier
2. **Supabase Auth**: Open-source, integrates with Supabase database, email/OAuth/magic links
3. **NextAuth.js (Auth.js)**: Open-source, flexible, self-hosted, supports many providers
4. **Firebase Auth**: Google's authentication service, free tier available
5. **Auth0**: Enterprise-grade, free tier available

**Selection criteria**:

- Free tier limits (monthly active users)
- Self-hosted vs managed service
- UI customization requirements
- Identity providers needed (Google, GitHub, Email, etc.)
- Privacy and data residency concerns

**Rationale**: Authentication is complex and security-critical. Using established providers reduces security risk and development time.

---

### Data Fetching & API Client

**Principle**: Choose based on rendering strategy and complexity

**For client components**:

- **TanStack Query (React Query)**: Industry standard for server state management
  - Features: Caching, background updates, optimistic updates, infinite queries
  - Best for: Complex data fetching, real-time updates, pagination

**For server components (Next.js)**:

- **Built-in fetch**: Use native fetch API with Next.js caching
- **Server Actions**: Use for mutations and form submissions

**For simple projects**:

- **Native fetch**: Simple HTTP requests without complex state management

**Rationale**: TanStack Query handles server state complexity (caching, revalidation, background updates). For simple cases, native fetch is sufficient.

---

### Database & Backend

**Principle**: Choose based on data model, scalability needs, and hosting preferences

**Popular options**:

1. **Prisma**: Type-safe ORM, excellent TypeScript support, supports SQL and MongoDB
2. **Drizzle ORM**: TypeScript-first, SQL-like syntax, lightweight and fast
3. **Supabase**: PostgreSQL database + auto-generated APIs + realtime subscriptions
4. **PlanetScale**: Serverless MySQL, generous free tier, Git-like workflows
5. **Neon**: Serverless PostgreSQL, auto-scaling, branching

**Selection criteria**:

- Data model (relational vs document)
- Free tier limits (storage, rows, connections)
- TypeScript support
- Developer experience
- Vendor lock-in concerns

**Rationale**: Modern database services provide free tiers suitable for personal projects. ORMs improve type safety and developer experience.

---

### Logging & Error Tracking

**Principle**: Choose based on features needed and budget

**Popular options**:

1. **Sentry**: Error tracking and performance monitoring, generous free tier
2. **LogRocket**: Session replay + error tracking + performance monitoring
3. **BetterStack (Logtail)**: Modern logging platform, excellent search
4. **Console logging**: Simple console-based logging for development

**For simple projects**:

- Use browser DevTools and console logging during development
- Add error tracking when project becomes production-critical

**Rationale**: Error tracking helps identify and fix issues quickly. Start simple, add observability as project grows.

---

### Analytics

**Principle**: Choose privacy-friendly options when possible

**Popular options**:

1. **Vercel Analytics**: Zero-config for Next.js on Vercel, privacy-friendly
2. **Plausible**: GDPR compliant, no cookies, self-hosted or cloud
3. **PostHog**: Open-source product analytics, session replay, feature flags
4. **Google Analytics 4**: Free, comprehensive, requires cookie consent

**Privacy considerations**:

- Cookie-less analytics (Vercel Analytics, Plausible)
- GDPR compliance requirements
- User consent management
- Data ownership (self-hosted vs cloud)

**Rationale**: Privacy-friendly analytics improve user trust and reduce legal compliance burden.

---

## Deployment Platforms

**Principle**: Choose based on framework, features needed, and cost

**Popular options**:

1. **Vercel**: Best for Next.js, zero-config, edge functions, unlimited personal projects
2. **Netlify**: Great for static sites, serverless functions, form handling
3. **Cloudflare Pages**: Edge deployment, unlimited bandwidth on free tier
4. **Railway**: Full-stack deployment, databases + apps, simple pricing
5. **Render**: Free static sites, PostgreSQL databases, background workers

**Selection criteria**:

- Framework compatibility (Next.js vs Vite)
- Free tier limits (bandwidth, build minutes)
- Geographic distribution (CDN, edge)
- Backend needs (databases, serverless functions)

**Rationale**: Modern platforms offer generous free tiers for personal projects. Zero-config deployment reduces operations overhead.

---

## Development Tools

### Code Quality

**RECOMMENDED**:

- **ESLint**: Catch code quality issues and bugs
- **Prettier**: Consistent code formatting
- **TypeScript**: Type safety and better IDE support
- **Husky + lint-staged**: Git hooks for pre-commit checks

**Rationale**: Automated code quality tools catch issues early and ensure consistency across team members or contributors.

---

### Testing

**RECOMMENDED**:

- **Vitest**: Fast unit testing, modern API, better DX than Jest
- **React Testing Library**: User-centric component testing
- **Playwright**: Cross-browser E2E testing
- **Cypress**: Alternative E2E testing with great DX

**Testing strategy**:

- Start with unit tests for critical logic
- Add integration tests for user flows
- Add E2E tests for critical paths as project matures

**Rationale**: Testing provides confidence for refactoring and prevents regressions. Start simple, add coverage as project grows.

---

## Environment Management

**Principle**: Use environment variables for configuration

**Best practices**:

- Use `.env.local` for local development (gitignored)
- Provide `.env.example` as template (committed)
- Validate environment variables at build/runtime
- Never commit secrets to version control
- Use platform-specific variable management for deployment

**Framework conventions**:

- Next.js: `NEXT_PUBLIC_` prefix for client-exposed variables
- Vite: `VITE_` prefix for client-exposed variables
- Server-only variables: No prefix, not accessible in client code

**Rationale**: Environment variables enable configuration per environment while keeping secrets secure.

---

## Free Tier Resources

### Hosting

- **Vercel**: Unlimited personal projects, 100GB bandwidth/month
- **Netlify**: 100GB bandwidth/month, 300 build minutes/month
- **Cloudflare Pages**: Unlimited bandwidth, 500 builds/month
- **Railway**: $5 credit/month
- **Render**: Free static sites, limited databases

### Databases

- **Supabase**: 500MB database, 1GB file storage, 50K monthly active users
- **PlanetScale**: 5GB storage, 1 billion row reads/month
- **Neon**: 10GB storage, unlimited projects
- **MongoDB Atlas**: 512MB storage

### Authentication

- **Clerk**: 10,000 monthly active users
- **Supabase Auth**: 50,000 monthly active users
- **Auth0**: 7,000 monthly active users
- **Firebase Auth**: Unlimited (pay for other services)

### Error Tracking

- **Sentry**: 5,000 events/month
- **BugSnag**: 7,500 events/month

### Analytics

- **Vercel Analytics**: 2,500 events/month
- **Plausible**: Self-hosted (free), cloud ($9/month)
- **PostHog**: 1 million events/month

**Rationale**: Free tiers enable building and deploying production-quality applications at zero cost.

---

## Licensing Principles

**RECOMMENDED** for open source projects:

- **MIT**: Most permissive, allows commercial use, simple
- **Apache 2.0**: Patent protection, requires attribution
- **GPL v3**: Copyleft, derivatives must be open source
- **ISC**: Similar to MIT, simpler wording

**License selection criteria**:

- Permissiveness level (MIT/Apache vs GPL)
- Patent grant requirements
- Commercial use allowance
- Derivative work requirements

**Project documentation**:

- Add LICENSE file to project root
- Specify license in package.json
- Include license information in README

**Rationale**: Clear licensing prevents legal issues and clarifies how others can use your code.

---

## Community & Learning Resources

### Official Documentation

- React: <https://react.dev>
- Next.js: <https://nextjs.org/docs>
- Vite: <https://vitejs.dev>
- TypeScript: <https://www.typescriptlang.org>
- TanStack Query: <https://tanstack.com/query>
- Tailwind CSS: <https://tailwindcss.com>

### Component Libraries

- shadcn/ui: <https://ui.shadcn.com>
- Radix UI: <https://www.radix-ui.com>
- Headless UI: <https://headlessui.com>
- MUI: <https://mui.com>
- Chakra UI: <https://chakra-ui.com>

### Learning Resources

- React Tutorial: <https://react.dev/learn>
- TypeScript Handbook: <https://www.typescriptlang.org/docs/handbook>
- Next.js Learn: <https://nextjs.org/learn>
- Web.dev: <https://web.dev/learn>
- JavaScript.info: <https://javascript.info>

### Communities

- React Discord: <https://discord.gg/react>
- Reactiflux: <https://www.reactiflux.com>
- Next.js Discord: <https://nextjs.org/discord>
- Reddit: r/reactjs, r/nextjs
- Dev.to: React community articles

**Rationale**: Active community provides support, learning resources, and keeps you updated on best practices.

---

## Project Philosophy

**Start Simple, Scale as Needed**:

- Don't over-engineer early projects
- Add complexity only when required
- Choose simple solutions first
- Optimize when you have performance problems (profile first)

**Developer Experience First**:

- Fast feedback loops (hot reload, fast builds)
- Good error messages and debugging
- Minimal configuration
- Modern tooling

**Cost-Effective Solutions**:

- Leverage free tiers
- Choose managed services over self-hosting (when free)
- Use serverless when possible (pay per use)
- Monitor usage to avoid surprise costs

**Learn by Building**:

- Build real projects to learn
- Contribute to open source
- Share your work with the community
- Iterate based on feedback

---

**Last Updated**: 2025-11-16
**Maintained by**: Open Source Community
**Contributing**: Suggestions welcome! Create an issue or PR in the guidelines repo.
