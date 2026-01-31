# Stage-Specific Prompt Templates for Modernization Workflow

This directory contains **4 stage-specific prompt templates** that inject legacy code context
into each stage of the Toolkit workflow.

## Template Injection

These templates are included in analyze prompts via `{{include:stage-prompt-templates/X-template.md}}`
syntax and are injected by the CLI at runtime. For example, in `06d-stage-prompts.md`:

```markdown
{{include:stage-prompt-templates/constitution-prompt-template.md}}
{{include:stage-prompt-templates/clarify-prompt-template.md}}
{{include:stage-prompt-templates/tasks-prompt-template.md}}
{{include:stage-prompt-templates/implement-prompt-template.md}}
```

**Note**: We do NOT generate prompts for the `specify` and `plan` stages. Instead, use
the paired spec documents directly, as they contain all the necessary information
without the redundant wrapper prompts.

## How to Use These Prompts

After running the analyze-project command, you'll have:

1. `functional-spec-legacy.md` - WHAT the legacy system does
2. `functional-spec-target.md` - WHAT the target system should do
3. `technical-spec-legacy.md` - HOW the legacy system is built
4. `technical-spec-target.md` - HOW to build the new system
5. `stage-prompts/` (this directory) - Guidance for each Toolkit stage

### Workflow Integration

When running each Toolkit stage, **prepend the corresponding stage prompt**
to your input. The prompt provides legacy code context and guidance.

**Example** (specify stage):

```text
Use the requirements from analysis/functional-spec-legacy.md section Section 5 (Functional Requirements).

Focus on CRITICAL features (FR-CRIT-*) for Phase 1:
- FR-CRIT-001: User Authentication (src/auth/login.js:34-89)
- FR-CRIT-002: Payment Processing (src/orders/payment.js:156-234)
- FR-CRIT-003: Audit Logging (src/audit/logger.js:12-34)

For detailed requirements, see functional-spec-legacy.md.
```

## Template Files

| File | Toolkit Stage | Purpose |
| ------ | --------------- | --------- |
| `constitution-prompt-template.md` | /speckitadv.constitution | Extract principles from legacy |
| ~~`specify-prompt-template.md`~~ | /speckitadv.specify | **Use `functional-spec-target.md` directly** |
| ~~`plan-prompt-template.md`~~ | /speckitadv.plan | **Use `technical-spec-target.md` directly** |
| `clarify-prompt-template.md` | /speckitadv.clarify | Use legacy code as source of truth |
| `tasks-prompt-template.md` | /speckitadv.tasks | Break down with legacy complexity |
| `implement-prompt-template.md` | /speckitadv.implement | Reference legacy code during implementation |

## Key Principle: "Legacy Code as Source of Truth"

For `clarify` and `implement` stages, the prompts include explicit instruction:

> **Consult legacy app <<path>> as the source of truth if the specification
> is underspecified, ambiguous, or requires further clarification.**

This prevents hallucination and ensures accurate modernization.

## Auto-Generated Content

Each stage prompt is **auto-generated** during the analyze-project workflow.
They contain:

- **Legacy Code References**: Actual file paths and line numbers
- **Critical Behaviors**: Must-preserve functionality
- **Modernization Guidance**: Target stack context
- **Ready-to-Paste**: Copy into Toolkit stage input

## Manual Editing

You can edit these prompts before using them if needed. They are Markdown files
generated from templates + AI analysis.
