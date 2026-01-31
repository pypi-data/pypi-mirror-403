---
stage: api
requires: components
outputs: "{wiki_dir}/api.md"
version: 2.1.0
---

# Stage 8: API Documentation

Generate comprehensive API endpoint documentation with routes, methods, parameters, request/response schemas, and examples.

## Prerequisites

- Stage 07 completed with components documented
- Mode: `{REPOIX_MODE}` (if "cli", convert MCP calls per AGENTS.md)
- Discovery cache loaded: LIMITS

## Critical Rules

| Rule | Action |
|------|--------|
| Components required | **MUST** verify {wiki_dir}/components/README.md exists |
| Search before skip | **MUST** search for endpoints before deciding to skip |
| Trace endpoints | **SHOULD** document request/response schemas when available |
| Skip if none | **MAY** skip if no API endpoints found (library projects) |

---

{{include:ai-cache-enforcement.md}}

## AI Context Cache: Check Cached Understanding

**[!] MANDATORY: Check cache status FIRST.**

```text
# [!] MANDATORY: Check cache status at stage start
get_understanding_stats(limit=50)

# Recall understanding for paths from stats output
recall_understanding(target="project")

# Use ACTUAL paths from YOUR get_understanding_stats output:
# recall_understanding(target="{path_from_stats}")  # if exists in stats

# IF found AND fresh: Use cached analysis to guide API documentation
# IF not found: Proceed with discovery, then MUST store findings
```

---

## Step 1: Verify Previous Stage

```bash
speckitadv deepwiki-update-state verify-stage --stage=08-api --wiki-dir={wiki_dir}
```

---

## Step 2: Load Discovery Cache

```bash
speckitadv deepwiki-update-state show --wiki-dir={wiki_dir}
# Extract: LIMITS = discovery_cache.project_size.limits
# Use LIMITS.endpoints for get_api_endpoints(limit=LIMITS.endpoints)
```

**MCP/CLI conversion (if REPOIX_MODE == "cli"):**

| MCP Call | CLI Equivalent |
|----------|----------------|
| `get_api_endpoints(limit=100)` | `civyk-repoix query get-api-endpoints --limit 100` |
| `search_code(query="@route", is_regex=true)` | `civyk-repoix query search-code --query "@route" --is-regex true` |
| `build_context_pack(task="...", token_budget=2000)` | `civyk-repoix query build-context-pack --task "..." --token-budget 2000` |

---

## Step 3: Find API Endpoints

```text
# Get all endpoints
get_api_endpoints(limit=200)
build_context_pack(task="document all API endpoints and routes", token_budget=2000)
get_components()

# Framework-specific routes
# Python (Flask/FastAPI)
search_code(query="@app.route|@app.get|@app.post|@router.get|@router.post", is_regex=true, limit=100)

# JavaScript (Express/NestJS)
search_code(query="express.Router|app.get|@Get|@Post|@Controller", is_regex=true, limit=100)

# Java (Spring)
search_code(query="@RequestMapping|@GetMapping|@PostMapping", is_regex=true, limit=100)

# Go (Gin/Echo/Fiber)
search_code(query="r.GET|r.POST|e.GET|e.POST", is_regex=true, limit=100)

# C#/.NET
search_code(query="\\[HttpGet\\]|\\[HttpPost\\]|\\[ApiController\\]", is_regex=true, limit=100)

# Ruby on Rails
search_code(query="resources :|get |post |put |delete ", is_regex=true, file_pattern="*routes*", limit=50)

# PHP Laravel
search_code(query="Route::get|Route::post|Route::resource", is_regex=true, limit=50)

# Rust (Actix, Axum, Rocket)
search_code(query="#\\[get|#\\[post|web::get|axum::Router", is_regex=true, limit=50)

# GraphQL
search_code(query="@Query|@Mutation|@Resolver|type Query", is_regex=true, limit=50)

# gRPC
list_files(pattern="**/*.proto", limit=50)

# WebSocket
search_code(query="@WebSocket|socket.on|@SubscribeMessage", is_regex=true, limit=50)
```

---

## Step 4: Trace Each Endpoint

For each endpoint:

```text
# FIRST: Check cached understanding for controller file
recall_understanding(target="<controller_file>")
# IF error (MCP connection failed): Fallback to manual file read
# IF found AND fresh:
#   -> Use cached endpoint analysis from key_points
#   -> Skip get_file_symbols, get_file_imports (already cached)
#   -> Jump to "Get DTOs/schemas" section
# IF not found OR stale: Proceed with full analysis below

# Find controller (skip if cache hit)
search_symbols(query="<ControllerName>", kind="class")
get_file_symbols(path="<controller_file>", kinds=["method"])
get_file_imports(path="<controller_file>")

# Read implementation (check cache first)
recall_understanding(target="<controller_file>")
# IF not cached: Read file: <controller_file>
# [!] NOW CALL store_understanding for the file above
# -> Extract route, parameters, validation, response format

# Get DTOs/schemas
search_symbols(query="%<EndpointName>%Dto", kind="class", limit=20)
search_symbols(query="%<EndpointName>%Schema", kind="class", limit=20)
recall_understanding(target="<dto_file>")
# IF not cached: Read file: <dto_file>
# [!] NOW CALL store_understanding for the file above

# Get examples from tests
get_related_files(path="<controller_file>", relationship_types=["test"])
recall_understanding(target="<test_file>")
# IF not cached: Read file: <test_file>
# [!] NOW CALL store_understanding for the file above

# Understand usage
get_callers(fqn="<method_fqn>", depth=2)

# Find duplicate endpoint patterns (consolidation candidates)
get_duplicate_code(source_only=true, similarity_threshold=0.7, limit=30)

# [!] MANDATORY: Store understanding for EACH file read above
store_understanding(
  scope="file",
  target="<controller_file>",
  purpose="API controller for <endpoint_group>",
  importance="high",
  key_points=["<routes>", "<auth_required>", "<response_format>"],
  gotchas=["<validation_rules>", "<error_codes>"],
  analysis="<detailed_logic_and_flow_explanation>",
  related_to=["<dto_files>", "<test_files>"]
)
store_understanding(
  scope="file",
  target="<dto_file>",
  purpose="DTOs/schemas for <endpoint_group>",
  importance="medium",
  key_points=["<fields>", "<validation>", "<serialization>"],
  gotchas=["<required_vs_optional>", "<nested_types>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
store_understanding(
  scope="file",
  target="<test_file>",
  purpose="API tests for <endpoint_group>",
  importance="medium",
  key_points=["<test_cases>", "<example_payloads>"],
  gotchas=["<edge_case_coverage>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Step 5: Generate Documentation

Write `{wiki_dir}/api.md` using this template:

{{include:wiki/api-template.md}}

**Fill placeholders with:** API overview, authentication mechanism, endpoints table, per-endpoint details (parameters, schemas, responses), error codes, rate limiting, versioning strategy.

---

## Step 6: Complete Stage

```bash
speckitadv deepwiki-update-state stage --stage=08-api --status=completed --artifacts="{wiki_dir}/api.md" --wiki-dir={wiki_dir}
```

---

## Output Format

```text
===========================================================
  STAGE COMPLETE: 08-api

  Generated: {wiki_dir}/api.md
  Endpoints: {count}
  Methods covered: GET, POST, PUT, DELETE

  AI Cache Efficiency:
    - Files read: <count_read>
    - Files cached (store_understanding): <count_stored>
    - Cache hits (found=true, fresh=true): <count_hits>

  Next: Run {next_command}
===========================================================
```

---

## Edge Cases

| Scenario | Action |
|----------|--------|
| No API endpoints | Skip stage (library project) |
| GraphQL instead of REST | Document schema and resolvers |
| gRPC/Protobuf | Document RPC methods and messages |
| WebSocket endpoints | Document event types and message formats |

---

## Next Stage

Run `{next_command}` - CLI auto-detects current stage and emits next prompt.
