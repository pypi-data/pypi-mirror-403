## Artifactory Dependency Validation (Conditional)

**Check configuration first:**

```bash
speckitadv search-lib --help 2>/dev/null && echo "Artifactory available"
```

**IF Artifactory is configured** (`artifactory.enabled = true` in `memory/config.json`):

For EACH proposed dependency/library, validate availability:

```bash
# Validate each dependency against corporate Artifactory
speckitadv search-lib <package-name>
```

**Exit Codes:**

| Code | Meaning | Action |
|------|---------|--------|
| 0 | FOUND | Library approved - include in plan |
| 1 | NOT FOUND | Library not in approved repos - document as blocker or find alternative |
| 2 | AUTH ERROR | Check credentials - alert user |
| 4 | SKIPPED | Artifactory not configured - proceed without validation |

**Validation Table Template:**

| Package | Version | Purpose | Artifactory Status |
|---------|---------|---------|-------------------|
| `<package>` | `<version>` | `<purpose>` | `[VERIFIED]` / `[NOT FOUND - needs approval]` / `[SKIPPED - not configured]` |

**IF Artifactory is NOT configured** (`artifactory.enabled = false` or not set):

- Skip validation
- Mark dependencies as `[UNVERIFIED - Artifactory not configured]`
- Document assumption that packages will be available from public registries

**Best Practices:**

1. Validate ALL external dependencies before finalizing design
2. For `NOT FOUND` results, check if the package name/spelling is correct
3. If package genuinely unavailable, propose alternatives that ARE in Artifactory
4. Document any packages requiring manual approval process
