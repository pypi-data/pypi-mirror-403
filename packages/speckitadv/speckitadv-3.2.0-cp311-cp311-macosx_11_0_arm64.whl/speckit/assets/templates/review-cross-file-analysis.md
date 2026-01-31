# Cross-File Analysis

**[!] Catches bugs single-file review misses.**

## Patterns to Check

| Pattern | Check | Tools |
|---------|-------|-------|
| Return types | Callers handle return correctly | `get_callers`, `get_references` |
| API contracts | All paths return consistent schema | `search_code`, `get_api_endpoints` |
| Feature wiring | New code registered/reachable | `get_dead_code`, `get_dependencies` |
| Breaking changes | Callers updated for signature changes | `analyze_impact` |
| DRY violations | New code duplicates existing logic | `get_duplicate_code(source_only=true)` |

## Language-Agnostic Bugs

- Caller iterates tuple/list directly instead of unpacking
- Optional/nullable not checked before use
- Async function not awaited
- Resource not closed/disposed
- Error type changed but catch not updated

## Output

```text
P1: [Category] - [file:line]
Issue: [description]
Fix: [solution]
```
