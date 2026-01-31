# Plan Stage Prompt (from Legacy Analysis)

**Input Source**: `.analysis/{project}/reports/technical-spec-target.md`
**Project**: <<PROJECT_NAME>>

---

## Instructions

This stage defines HOW to build the modernized system.
Use `technical-spec-target.md` from the `.analysis/{project}/reports/` directory
for target architecture and tech stack.

---

## Ready-to-Paste Prompt

```text
PLAN architecture for modernization of <<PROJECT_NAME>>.

BASE ARCHITECTURE: Use .analysis/{project}/reports/technical-spec-target.md

TARGET TECH STACK (from user preferences + LTS):
- Language: <<USER_CHOICE_LANGUAGE>> (<<LTS_VERSION>>)
- Database: <<USER_CHOICE_DATABASE>> (<<LTS_VERSION>>)
- Message Bus: <<USER_CHOICE_MESSAGE_BUS>>
- Deployment: <<USER_CHOICE_DEPLOYMENT>>
- IaC: <<USER_CHOICE_IAC>>
- Containerization: <<USER_CHOICE_CONTAINERIZATION>>
- Observability: <<USER_CHOICE_OBSERVABILITY>>
- Security (Auth): <<USER_CHOICE_SECURITY>>
- Testing: <<USER_CHOICE_TESTING>>

Full stack details in technical-spec-target.md Section 8.

ARCHITECTURE PATTERN: <<from technical-spec-target.md Section 2>>
- Legacy: <<current pattern>>
- Target: <<chosen pattern>> (rationale: <<why>>)

MIGRATION STRATEGY: <<from technical-spec-target.md Section 12>>
- Approach: Strangler Fig / Blue-Green / <<other>>
- Phasing: P1 (months 1-3), P2 (months 4-6), P3 (months 7-9)

NFR TARGETS (measurable SLO/SLI): See technical-spec-target.md Section 9
- Performance: p95 < <<target>>ms
- Availability: <<target>>% uptime
- Scalability: <<target>> concurrent users

COMPONENT DESIGN: See technical-spec-target.md Section 5
<<List components with responsibilities>>

DATA MIGRATION: See technical-spec-target.md Section 7
- Strategy: <<dual-write | backfill | <<other>>>>
- Schema mapping: Legacy -> Target

For detailed architecture, see .analysis/{project}/reports/technical-spec-target.md.
Use phase-colored Mermaid diagram from technical-spec-target.md Section 4.
```
