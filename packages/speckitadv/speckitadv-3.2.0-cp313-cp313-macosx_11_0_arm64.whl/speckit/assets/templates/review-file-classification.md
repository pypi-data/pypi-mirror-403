# File Classification

| Category | Patterns |
|----------|----------|
| TEST | `test_*.py`, `*.test.ts`, `*Test.java`, `*_spec.rb`, `tests/`, `__tests__/` |
| CONFIG | `.json`, `.yaml`, `.toml`, `.env`, `Dockerfile`, `*config*` |
| DOCS | `.md`, `.rst`, `README*`, `CHANGELOG*` |
| SOURCE | All other code files (`.py`, `.ts`, `.java`, `.go`, etc.) |

Classify by extension/path first. If unknown, check first 10 lines for test/API/config patterns.
