# Abstraction Recommendations: <<CONCERN_TYPE>>

**Project**: <<PROJECT_NAME>>
**Analysis Date**: <<ANALYSIS_DATE>>
**Current Abstraction Level**: <<HIGH / MEDIUM / LOW>>
**Concern Type**: <<e.g., Authentication/Authorization>>

---

## Executive Summary

**Current Situation**: <<Brief description of current abstraction state>>

**Recommendation**: <<IF HIGH/MEDIUM: "Maintain current abstractions" | IF LOW: "Refactor to introduce abstractions before migration">>

**Impact**: <<How abstraction quality affects migration difficulty>>

**Effort to Improve**: <<IF LOW: Time estimate for refactoring | IF HIGH/MEDIUM: "Minimal - abstractions already adequate">>

---

<<IF ABSTRACTION_LEVEL = HIGH>>

## [ok] Current Abstractions: HIGH Quality

**Congratulations!** Your <<CONCERN_TYPE>> concern is well-abstracted and ready for migration.

### What's Working Well

**Strong Abstraction Indicators Found**:

- [ok] Single interface/contract serving all consumers
- [ok] Dependency injection used throughout
- [ok] No direct implementation imports in consumers
- [ok] Configuration-driven behavior
- [ok] Clear separation: Interface -> Implementation -> Consumers

**Evidence**:
<<List specific examples with file:line references>>:

- Interface: <<IInterfaceName>> at <<file:line>>
- Implementation: <<ClassName>> at <<file:line>>
- DI Registration: <<file:line>>
- Consumer example: <<file:line>> (imports interface, not implementation)

### Recommendations for Maintenance

While your abstractions are excellent, consider these best practices for maintaining quality:

1. **Preserve Interface Stability**
   - Avoid breaking changes to <<IInterfaceName>> interface
   - Use interface versioning if breaking changes are needed
   - Document interface contracts clearly

2. **Continue Using Dependency Injection**
   - All new consumers should use DI to resolve <<CONCERN_TYPE>> services
   - Avoid `new ConcreteClass()` instantiation in consumers
   - Register new implementations in DI container: <<file:line>>

3. **Externalize Configuration**
   - Keep all <<CONCERN_TYPE>> config in: <<config-file:line>>
   - Avoid hardcoding values in implementation
   - Use environment-specific configs (dev/staging/prod)

4. **Documentation**
   - Document interface contracts (parameters, return values, exceptions)
   - Provide migration guide for switching implementations
   - Maintain ADR (Architecture Decision Record) for abstraction choices

### Migration Impact: LOW RISK

**With HIGH abstraction, migration will be straightforward**:

- [ok] Implement new provider class (e.g., <<NewProviderName>>)
- [ok] Register in DI container
- [ok] Use feature flags to gradually switch consumers
- [ok] No changes needed in consumer code

**Recommended Strategy**: STRANGLER_FIG pattern
**Estimated Effort**: 2-4 weeks
**Risk Level**: LOW

---

<<ELSE IF ABSTRACTION_LEVEL = MEDIUM>>

## [!] Current Abstractions: MEDIUM Quality

Your <<CONCERN_TYPE>> concern has partial abstractions. Some improvements will reduce migration risk.

### What's Working

**Positive Indicators Found**:

- [ok] Multiple entry points with consistent patterns
- [ok] Some use of interfaces (partial coverage)
- [ok] Dependency injection used in some areas

**Evidence**:
<<List what's working well with file:line references>>:

- Abstraction found: <<file:line>>
- DI usage: <<file:line>>
- ...

### What Needs Improvement

**Areas of Concern**:

- [!] Some direct dependencies on concrete implementations
- [!] Mix of DI and manual instantiation
- [!] Partial interface usage (<<X%>> of consumers)

**Evidence**:
<<List problems with file:line references>>:

- Direct import: <<file:line>> imports <<ConcreteClass>> instead of <<IInterface>>
- Manual instantiation: <<file:line>> uses `new ConcreteClass()`
- ...

### Recommendations for Improvement

**Priority 1: Complete Interface Coverage** (1-2 weeks)

**Goal**: Ensure ALL consumers depend on interface, not concrete implementation.

**Steps**:

1. **Audit Current Consumers**
   - Files using interface: <<List>>
   - Files using concrete class: <<List>> <- THESE need refactoring

2. **Refactor Direct Dependencies**
   - Change imports from `import { ConcreteClass }` to `import { IInterface }`
   - Update constructor/property signatures to use interface type
   - Example refactoring at: <<file:line>>

3. **Verify with Static Analysis**
   - Run linter/compiler to detect direct imports
   - Ensure no `import { <<ConcreteClassName>> }` in consumer code

**Priority 2: Standardize Dependency Injection** (1-2 weeks)

**Goal**: Replace all manual instantiation with DI.

**Current State**:

- DI coverage: <<X%>> of consumers
- Manual instantiation: <<Y%>> of consumers <- THESE need refactoring

**Steps**:

1. **Identify Manual Instantiation**
   - Search for: `new <<ClassName>>()`
   - Found at: <<List file:line>>

2. **Replace with DI**
   - Constructor injection pattern:

     ```typescript
     constructor(private readonly service: IInterface) {}
     ```

   - Register in DI container: <<file:line>>

3. **Testing**
   - Verify all consumers still work
   - Unit tests should mock interface, not concrete class

**Priority 3: Configuration Externalization** (Optional, 1 week)

If config values are hardcoded:

- Move to config file: <<recommended-location>>
- Use environment variables for secrets
- Document all config options

### Migration Impact: MEDIUM RISK

**With MEDIUM abstraction, migration requires moderate care**:

- [!] Some refactoring needed before migration
- [!] Test all consumers after switching implementation
- [!] Gradual rollout recommended

**Recommended Strategy**: ADAPTER_PATTERN
**Estimated Effort**: 4-8 weeks (2-3 weeks refactoring + 2-5 weeks migration)
**Risk Level**: MEDIUM

**Refactoring Roadmap**:

- **Weeks 1-2**: Complete interface coverage (Priority 1)
- **Weeks 3-4**: Standardize DI (Priority 2)
- **Weeks 5-8**: Implement migration with adapter pattern

---

<<ELSE IF ABSTRACTION_LEVEL = LOW>>

## [x] Current Abstractions: LOW Quality

**CRITICAL**: Your <<CONCERN_TYPE>> concern lacks proper abstractions. Migration will be difficult and risky without refactoring.

### Problems Identified

**Low Abstraction Indicators Found**:

- [x] No interface/contract definitions
- [x] Direct imports of implementation everywhere (tight coupling)
- [x] Hardcoded dependencies (`new ConcreteClass()` throughout)
- [x] Implementation details leak into business logic
- [x] No dependency injection

**Evidence**:
<<List all problems with file:line references>>:

- Direct implementation usage: <<file:line>>
- Hardcoded instantiation: <<file:line>>
- Leaked implementation details: <<file:line>>
- ... (comprehensive list)

**Impact**:

- : Migration will require touching <<X%>> of codebase
- : High risk of breaking existing functionality
- : Difficult to test in isolation
- : Cannot run old and new implementations side-by-side

### Recommended Abstractions to Introduce

**Before attempting migration, you MUST introduce proper abstractions.**

---

#### Abstraction 1: Interface/Contract Definition

**Create**: `I<<ConcernName>>Service` interface

**Location**: `src/interfaces/I<<ConcernName>>Service.ts` (or appropriate for your tech stack)

**Interface Should Define**:

Based on analysis of current implementation (<<file:line>>), the interface should include:

```typescript
// EXAMPLE STRUCTURE (adapt to your language/framework)
interface I<<ConcernName>>Service {
  // Core methods identified in current implementation:
  <<method1>>(<<params>>): <<returnType>>;
  <<method2>>(<<params>>): <<returnType>>;
  // ... (list all public methods currently used)
}
```

**Methods to Abstract** (extracted from codebase):
<<List all current public methods/functions with evidence>>:

- `<<methodName>>()` - Used at: <<file:line>>, <<file:line>>
- ... (comprehensive list)

**Design Principles**:

- [ok] Interface should define WHAT, not HOW
- [ok] Use dependency inversion: depend on interface, not concrete class
- [ok] Keep interface stable (breaking changes are expensive)
- [ok] Document contracts (preconditions, postconditions, exceptions)

---

#### Abstraction 2: Implementation Wrapper

**Create**: Wrapper class that implements the interface

**Current Implementation**: <<ConcreteClass>> at <<file:line>>

**New Structure**:

```text
1. I<<ConcernName>>Service interface (contract)
2. <<Current>>Provider implements I<<ConcernName>>Service (wraps current logic)
3. <<Target>>Provider implements I<<ConcernName>>Service (future migration)
```

**Steps**:

1. **Extract Current Logic** into `<<Current>>Provider` class
   - Move code from: <<file:line>>
   - Implement `I<<ConcernName>>Service` interface
   - Keep logic IDENTICAL to current implementation (no changes)

2. **Verify Behavior Unchanged**
   - Run all existing tests
   - No functionality should change (pure refactoring)

---

#### Abstraction 3: Dependency Injection Setup

**Goal**: Replace all `new ConcreteClass()` with DI.

**Current State**:
<<List all manual instantiation locations>>:

- <<file:line>> - `new ConcreteClass()`
- ... (comprehensive list)

**DI Framework Recommendation**:
<<Recommend appropriate DI framework for tech stack>>:

- **Node.js/TypeScript**: NestJS DI, InversifyJS, tsyringe
- **Java**: Spring Framework, Google Guice
- **.NET**: Built-in DI (Microsoft.Extensions.DependencyInjection)
- **Python**: dependency-injector, injector

**DI Registration**:

```typescript
// EXAMPLE (adapt to your framework)
container.register(I<<ConcernName>>Service, <<Current>>Provider);
```

**Consumer Refactoring**:

**BEFORE** (current, tightly coupled):

```typescript
class UserController {
  authenticate() {
    const service = new ConcreteClass(); // [x] Tight coupling
    service.doSomething();
  }
}
```

**AFTER** (with DI, loose coupling):

```typescript
class UserController {
  constructor(private service: I<<ConcernName>>Service) {} // [ok] Depends on interface

  authenticate() {
    this.service.doSomething();
  }
}
```

**Files Needing Refactoring**:
<<List all consumer files>>:

- [ ] <<file:line>> - Replace manual instantiation with DI
- [ ] <<file:line>>
- ... (checklist of all files)

**Total Files to Refactor**: <<N>> files

---

#### Abstraction 4: Configuration Externalization

**Goal**: Move all hardcoded values to configuration.

**Current Hardcoded Values Found**:
<<List all hardcoded config with file:line>>:

- `<<value>>` at <<file:line>> (e.g., "JWT secret key")
- ... (comprehensive list)

**Recommended Config Structure**:

```yaml
# config/<<concern>>.yml (or appropriate for your stack)
<<concern>>:
  provider: <<current>>  # Can be changed to <<target>> after migration
  <<setting1>>: <<value>>
  <<setting2>>: <<value>>
  # ... (all extracted config)
```

**Environment-Specific Configs**:

- `config/<<concern>>.dev.yml` - Development
- `config/<<concern>>.staging.yml` - Staging
- `config/<<concern>>.prod.yml` - Production

**Benefits**:

- [ok] Easy to change provider without code changes
- [ok] Different configs per environment
- [ok] Secrets in environment variables (not code)

---

### Refactoring Roadmap

**RECOMMENDATION**: Refactor FIRST, then migrate.

**Timeline**: 6-8 weeks refactoring + 4-8 weeks migration = **10-16 weeks total**

**Phase 1: Extract Interfaces & Contracts** (2-3 weeks)

**Week 1-2**: Interface Definition

- [ ] Define `I<<ConcernName>>Service` interface
- [ ] Document all methods and contracts
- [ ] Review with team

**Week 2-3**: Wrapper Implementation

- [ ] Create `<<Current>>Provider` implementing interface
- [ ] Move existing logic to wrapper (no functionality changes)
- [ ] Run full test suite - verify no regressions

**Phase 2: Implement Dependency Injection** (2-3 weeks)

**Week 3-4**: DI Setup

- [ ] Choose and configure DI framework
- [ ] Register `I<<ConcernName>>Service` -> `<<Current>>Provider`
- [ ] Create integration tests

**Week 4-5**: Consumer Refactoring

- [ ] Refactor consumers to use DI (<<N>> files)
- [ ] Remove all `new ConcreteClass()` instantiation
- [ ] Test each refactored file

**Week 5-6**: Verification

- [ ] Run full test suite
- [ ] Code review all changes
- [ ] Deploy to staging environment
- [ ] Run integration tests in staging

**Phase 3: Externalize Configuration** (1-2 weeks)

**Week 6-7**: Config Extraction

- [ ] Create config files (dev/staging/prod)
- [ ] Extract hardcoded values to config
- [ ] Use environment variables for secrets
- [ ] Test with different configs

**Phase 4: Ready for Migration** (Week 8+)

At this point:

- [ok] Interface defined and used by all consumers
- [ok] DI setup complete
- [ok] Configuration externalized
- [ok] **Ready to implement <<Target>>Provider**

**Future Migration Steps**:

1. Implement `<<Target>>Provider` (implements same `I<<ConcernName>>Service` interface)
2. Register in DI container
3. Use feature flags to gradually switch from `<<Current>>Provider` to `<<Target>>Provider`
4. No changes needed in consumer code (they depend on interface)

---

### Migration Impact After Refactoring

**Current State (LOW abstraction)**:

- [x] Direct migration: 3-6 months, HIGH risk
- [x] Would require touching <<X%>> of codebase

**After Refactoring (HIGH abstraction)**:

- [ok] Migration: 2-4 weeks, LOW risk
- [ok] Only need to implement new provider
- [ok] Consumers unchanged (depend on interface)

**ROI Analysis**:

- **Refactoring Investment**: 6-8 weeks
- **Migration Savings**: 3-6 months -> 2-4 weeks (saves 2-5 months)
- **Long-term Benefit**: Future migrations become trivial
- **Risk Reduction**: HIGH -> LOW risk

---

### Cost-Benefit Analysis

#### Option A: Direct Migration (Not Recommended)

- [time] **Time**: 3-6 months
- [!] **Risk**: HIGH (likely bugs, breaking changes)
- [$] **Cost**: High (team time + bug fixes + rollbacks)
- [-] **Technical Debt**: Increases (still tightly coupled after migration)

#### Option B: Refactor First, Then Migrate (Recommended)

- [time] **Time**: 10-16 weeks total (6-8 refactor + 4-8 migrate)
- [ok] **Risk**: LOW (clean separation of concerns)
- [$] **Cost**: Moderate upfront, low long-term
- [+] **Technical Debt**: Decreases (better architecture)
- [bonus] **Bonus**: Future migrations become easy

**Recommendation**: **Option B** - The refactoring investment pays off immediately and provides long-term benefits.

---

<<END IF>>

## Summary & Next Steps

### Key Takeaways

**Current Abstraction Level**: <<HIGH / MEDIUM / LOW>>

<<IF HIGH>>:

- [ok] Your abstractions are excellent - ready for migration
- [ok] Follow maintenance best practices
- [ok] Proceed with STRANGLER_FIG migration strategy

<<ELSE IF MEDIUM>>:

- [!] Some refactoring recommended before migration
- [!] Focus on completing interface coverage and standardizing DI
- [!] 2-3 weeks refactoring reduces migration risk significantly

<<ELSE IF LOW>>:

- [x] **CRITICAL**: Refactoring required before migration
- [x] 6-8 weeks refactoring investment
- [x] Without refactoring, migration is HIGH risk and will take 3-6 months
- [ok] WITH refactoring, migration becomes LOW risk and takes 2-4 weeks

### Immediate Actions

1. **Review this document** with technical team
2. **Validate recommendations** - Do they fit your architecture?
3. **Make decision**:
   - <<IF LOW>>: Approve refactoring roadmap (6-8 weeks) vs. attempt direct migration (3-6 months, HIGH risk)
   - <<IF MEDIUM>>: Approve 2-3 weeks refactoring vs. proceed with current abstractions (MEDIUM risk)
   - <<IF HIGH>>: Proceed with migration (LOW risk)
4. **Read concern-migration-plan.md** for detailed migration steps
5. **Assign ownership** - Who will lead refactoring (if needed) and migration?

### Questions for Decision-Makers

**For LOW Abstraction Projects**:

- [ ] Are we willing to invest 6-8 weeks in refactoring before migration?
- [ ] Do we understand the risk of direct migration without refactoring?
- [ ] Do we value long-term maintainability over short-term speed?

**For MEDIUM Abstraction Projects**:

- [ ] Can we allocate 2-3 weeks for abstraction improvements?
- [ ] Are we comfortable with MEDIUM risk if we skip refactoring?

**For HIGH Abstraction Projects**:

- [ ] Do we agree that current abstractions are sufficient?
- [ ] Are we ready to proceed with migration?

---

**Document Version**: 1.0
**Template Version**: Phase 9 - Cross-Cutting Concern Analysis
**Generated By**: Spec Kit Analyze Project Command
