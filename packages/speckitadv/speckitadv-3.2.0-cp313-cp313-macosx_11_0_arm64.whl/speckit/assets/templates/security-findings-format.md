# Security Findings Format

**MUST: Report security issues with >80% confidence of actual exploitability.**

Focus on impact: unauthorized access, data breaches, system compromise.

## Required Fields

For each security finding, include:

| Field | Description |
|-------|-------------|
| Severity | HIGH/MEDIUM/LOW |
| Location | file:line |
| Category | Auth bypass, injection, secrets exposure, etc. |
| Description | What the vulnerability is |
| Exploit Scenario | How an attacker could exploit it |
| Recommendation | How to fix it |

## Severity Levels

| Level | Criteria |
|-------|----------|
| HIGH | Directly exploitable (RCE, data breach, auth bypass) |
| MEDIUM | Requires specific conditions, significant impact |
| LOW | Defense-in-depth, lower impact |

## Confidence Threshold

- 0.9-1.0: Certain exploit path
- 0.8-0.9: Clear vulnerability pattern
- 0.7-0.8: Suspicious, specific conditions needed
- **Below 0.7: Do NOT report** (too speculative)

## Do NOT Flag

- Denial of Service vulnerabilities
- Secrets/credentials stored on disk (outside code)
- Rate limiting concerns
- Theoretical race conditions
- Outdated library issues (belongs in dependency audit)
- Test-only files
- Log spoofing
- Documentation files
- Lack of audit logs

## Example Format

```text
[!] HIGH: {category} - {file:line}
    Description: {what the vulnerability is}
    Exploit: {how an attacker could exploit it}
    Fix: {recommendation}
```
