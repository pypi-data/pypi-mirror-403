# Testing Quick Reference

## Test Pyramid

| Level | % | Speed | Use For |
|-------|---|-------|---------|
| Unit | 60-70% | <100ms | Pure functions, logic |
| Integration | 20-30% | <1s | DB, APIs, services |
| E2E | 5-10% | Slow | Critical user flows |

## FIRST Principles

- **F**ast: <100ms unit, <1s integration
- **I**ndependent: No shared state
- **R**epeatable: Same result every time
- **S**elf-validating: Clear pass/fail
- **T**imely: Written with code

## AAA Pattern

```text
Arrange -> Act -> Assert
```

## Test Doubles

| Type | Use |
|------|-----|
| Stub | Canned responses |
| Mock | Verify calls |
| Fake | In-memory impl |
| Spy | Record calls |

## Edge Cases

- Null/empty, boundaries (0, 1, max), errors, unicode

## Naming

`test_[function]_[scenario]_[expected]`
