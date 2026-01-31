# Node.js Personal/Public Profile Overrides

**Profile**: Personal/Public Open Source
**Stack**: Node.js
**Version**: 3.0 (Principle-Based)
**Last Updated**: 2025-11-16

> **Note**: This file contains only personal/public project-specific overrides. Base guidelines are inherited from `base/nodejs-base.md`.
> **Philosophy**: These overrides define WHAT personal Node.js projects benefit from and WHY, not HOW to implement them. Prioritize developer experience, community packages, and cost-effective solutions.

---

## Scaffolding Principles

**RECOMMENDED** scaffolding approaches:

- **Express Generator**: Traditional Express setup for REST APIs
- **Fastify CLI**: High-performance framework with excellent TypeScript support
- **NestJS CLI**: Enterprise framework for large applications
- **Minimal setup**: Simple server file for learning and small projects

**Options by project type**:

- REST API → Express or Fastify
- GraphQL API → Apollo Server or Mercurius
- Full-stack framework → NestJS or AdonisJS
- Microservices → Fastify or custom minimal setup
- Real-time → Socket.io or WebSocket

**Rationale**: Modern Node.js frameworks provide excellent developer experience, fast iteration, and production-ready features.

---

## Package Registry Principles

**RECOMMENDED**:

- Use official npm registry (npmjs.org) as primary source
- Consider pnpm for faster installs and disk space efficiency
- Consider bun for ultra-fast package management and runtime
- Run security audits regularly to check for vulnerabilities

**Security practices**:

- Run `npm audit` regularly
- Use automated dependency updates (Dependabot, Renovate)
- Review package.json for unused dependencies
- Check package popularity and maintenance status before installing
- Verify package authenticity (check GitHub stars, npm downloads, maintainers)

**Rationale**: Public npm registry provides access to vast ecosystem. Modern package managers improve performance and disk usage.

---

## Recommended Library Categories

### Framework & Web Server

**Principle**: Choose based on performance needs, learning curve, and project complexity

**Popular options**:

1. **Express**: Most popular, largest ecosystem, traditional middleware approach
2. **Fastify**: High performance, schema validation, modern async/await patterns
3. **NestJS**: TypeScript-first, dependency injection, Angular-inspired architecture
4. **Koa**: Minimalist, async/await-first, created by Express team
5. **Hapi**: Configuration-driven, enterprise features, plugin system

**Selection criteria**:

- Performance requirements
- Team familiarity
- Ecosystem and plugin availability
- TypeScript support
- Project complexity and size

**Rationale**: Different frameworks excel at different use cases. Choose based on project requirements and team expertise.

---

### Database & ORM

**Principle**: Choose based on data model, type safety needs, and hosting preferences

**Popular options**:

1. **Prisma**: Type-safe ORM, excellent TypeScript support, supports SQL and MongoDB
2. **Drizzle ORM**: TypeScript-first, SQL-like syntax, lightweight and performant
3. **TypeORM**: Mature, supports multiple databases, Active Record or Data Mapper patterns
4. **Mongoose**: MongoDB-specific, schema-based, rich plugin ecosystem
5. **Sequelize**: Traditional ORM for SQL databases

**Database services**:

- **Supabase**: PostgreSQL + auto-generated APIs + realtime subscriptions
- **PlanetScale**: Serverless MySQL, generous free tier
- **Neon**: Serverless PostgreSQL, auto-scaling
- **MongoDB Atlas**: Managed MongoDB, free tier available
- **SQLite**: Embedded database for development and simple apps

**Selection criteria**:

- Data model (relational vs document)
- Free tier limits
- TypeScript support
- Developer experience
- Migration tooling

**Rationale**: Modern ORMs provide type safety and excellent developer experience. Database services offer free tiers suitable for personal projects.

---

### Authentication & Authorization

**Principle**: Choose based on ease of use, features needed, and budget

**Popular options**:

1. **Passport.js**: Flexible authentication middleware, 500+ strategies
2. **JWT (jsonwebtoken)**: Simple JWT token generation and verification
3. **Auth0**: Managed authentication service, free tier available
4. **Clerk**: Drop-in authentication with beautiful UI
5. **Supabase Auth**: Open-source, integrates with Supabase database

**Selection criteria**:

- Self-hosted vs managed service
- Authentication strategies needed (local, OAuth, SAML)
- Free tier limits
- UI requirements (pre-built vs custom)

**Rationale**: Authentication is security-critical. Using established libraries and services reduces security risk.

---

### Logging & Error Tracking

**Principle**: Choose based on features needed and budget

**Popular options**:

1. **Pino**: Fast structured logging, low overhead
2. **Winston**: Feature-rich logging library, multiple transports
3. **Sentry**: Error tracking and performance monitoring, free tier available
4. **BetterStack (Logtail)**: Modern logging platform
5. **Console logging**: Simple for development

**For simple projects**:

- Use console logging during development
- Add structured logging (Pino, Winston) when needed
- Add error tracking (Sentry) when project becomes production-critical

**Rationale**: Start simple, add observability as project grows. Structured logging enables better debugging and monitoring.

---

### Validation & Schema

**Principle**: Validate all inputs for security and data integrity

**Popular options**:

1. **Zod**: TypeScript-first schema validation
2. **Joi**: Powerful object schema validation
3. **Yup**: Simple and expressive schema validation
4. **class-validator**: Decorator-based validation for TypeScript classes
5. **Ajv**: Fast JSON schema validation

**Rationale**: Input validation prevents security vulnerabilities and data corruption. Type-safe validation improves developer experience.

---

### Testing

**Principle**: Start with unit tests, add integration and E2E tests as project matures

**Popular options**:

1. **Vitest**: Fast unit testing, modern API, better DX than Jest
2. **Jest**: Mature testing framework, large ecosystem
3. **Supertest**: HTTP assertion library for API testing
4. **Playwright**: E2E testing across browsers
5. **Mocha + Chai**: Traditional testing combination

**Testing strategy**:

- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical user flows

**Rationale**: Testing provides confidence for refactoring and prevents regressions. Modern testing tools improve developer experience.

---

### Utilities

**Common utilities**:

- **date-fns** or **dayjs**: Date manipulation (avoid moment.js - deprecated)
- **lodash-es**: Utility functions (tree-shakeable version)
- **dotenv**: Environment variable loading
- **cors**: CORS middleware
- **helmet**: Security headers middleware
- **express-rate-limit** or **fastify-rate-limit**: Rate limiting

**Rationale**: Well-maintained utilities reduce boilerplate and improve code quality.

---

## Deployment Platforms

**Principle**: Choose based on runtime needs, features, and cost

**Popular options**:

1. **Railway**: Full-stack deployment, databases + apps, $5 credit/month free
2. **Render**: Free tier for web services, background workers, PostgreSQL databases
3. **Fly.io**: Global edge deployment, generous free tier
4. **Heroku**: Simple deployment, add-ons ecosystem (paid)
5. **Vercel** (for serverless): Serverless functions, edge runtime
6. **DigitalOcean App Platform**: Simple deployment, predictable pricing

**Self-hosted options**:

- **Docker + VPS**: Full control, lowest cost for high traffic
- **AWS EC2/ECS**: Flexible, pay-per-use
- **Azure App Service**: Integrated with Azure ecosystem

**Selection criteria**:

- Free tier limits (hours, memory, bandwidth)
- Geographic distribution
- Database needs
- Scaling requirements
- Pricing model

**Rationale**: Modern platforms offer generous free tiers for personal projects. Zero-config deployment reduces operations overhead.

---

## Development Tools

### Code Quality

**RECOMMENDED**:

- **ESLint**: Catch code quality issues and bugs
- **Prettier**: Consistent code formatting
- **TypeScript**: Type safety and better IDE support
- **Husky + lint-staged**: Git hooks for pre-commit checks
- **ts-node** or **tsx**: Run TypeScript directly

**Rationale**: Automated code quality tools catch issues early and ensure consistency.

---

### Hot Reload / Development

**RECOMMENDED**:

- **nodemon**: Auto-restart on file changes
- **tsx**: Fast TypeScript execution with hot reload
- **ts-node-dev**: TypeScript development server

**Rationale**: Fast feedback loops improve developer productivity.

---

## Environment Management

**Principle**: Use environment variables for configuration

**Best practices**:

- Use `.env` file for local development (gitignored)
- Provide `.env.example` as template (committed)
- Use `dotenv` package to load variables
- Validate environment variables at startup
- Never commit secrets to version control

**Environment tiers**:

- Development: Local development with `.env`
- Staging: Test environment with production-like data
- Production: Live environment with real data

**Rationale**: Environment variables enable configuration per environment while keeping secrets secure.

---

## Free Tier Resources

### Hosting

- **Railway**: $5 credit/month
- **Render**: Free web services (750 hours/month), PostgreSQL
- **Fly.io**: Free tier with 3 VMs
- **Vercel**: Serverless functions (100GB bandwidth)

### Databases

- **Supabase**: 500MB PostgreSQL, 1GB file storage
- **PlanetScale**: 5GB storage, 1 billion row reads/month
- **Neon**: 10GB PostgreSQL storage
- **MongoDB Atlas**: 512MB storage
- **SQLite**: Free embedded database

### Error Tracking

- **Sentry**: 5,000 events/month
- **BugSnag**: 7,500 events/month

### Monitoring

- **Better Uptime**: 10 monitors
- **UptimeRobot**: 50 monitors

**Rationale**: Free tiers enable building and deploying production-quality applications at zero cost.

---

## Project Philosophy

**Start Simple, Scale as Needed**:

- Don't over-engineer early projects
- Add complexity only when required
- Choose simple solutions first
- Profile before optimizing

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

## Community & Learning Resources

### Official Documentation

- Node.js: <https://nodejs.org/docs>
- Express: <https://expressjs.com>
- Fastify: <https://www.fastify.io>
- NestJS: <https://nestjs.com>
- TypeScript: <https://www.typescriptlang.org>

### Popular Libraries

- Prisma: <https://www.prisma.io>
- Zod: <https://zod.dev>
- Passport.js: <https://www.passportjs.org>
- Pino: <https://getpino.io>

### Learning Resources

- NodeSchool: <https://nodeschool.io>
- Node.js Best Practices: <https://github.com/goldbergyoni/nodebestpractices>
- JavaScript.info: <https://javascript.info>

### Communities

- Node.js Discord
- Reddit: r/node, r/javascript
- Dev.to: Node.js community articles
- Stack Overflow

**Rationale**: Active community provides support, learning resources, and keeps you updated on best practices.

---

**Last Updated**: 2025-11-16
**Maintained by**: Open Source Community
**Contributing**: Suggestions welcome! Create an issue or PR in the guidelines repo.
