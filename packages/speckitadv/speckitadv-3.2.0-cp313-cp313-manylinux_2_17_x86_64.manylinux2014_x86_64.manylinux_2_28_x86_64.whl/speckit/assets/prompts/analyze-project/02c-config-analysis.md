---
stage: file_analysis_phase3
requires: 02b-deep-dive complete
outputs: config_analysis
version: 3.6.0
time_allocation: 15%
---

# Stage 2C: Configuration Analysis (Phase 3)

## Purpose

Analyze ALL configuration files completely using CLI-based discovery followed by deep file reading. Configuration contains crucial information about database connections, external services, security settings, and environment-specific behavior.

**Time Allocation:** 15% of file analysis effort
**Coverage Target:** 100% of configuration files

---

{{include:strict-execution-mode.md}}

{{include:analyze-state-management.md}}

{{include:analyze-file-write-policy.md}}

{{include:ai-cache-enforcement.md}}

---

## AI Context Cache: Recall Earlier Analysis

Before analyzing configs, recall cached understanding from earlier stages:

```text
# FIRST: Discover ALL cached entries (project, modules, files)
get_understanding_stats(limit=50)
# Review output to identify ALL cached targets and their scopes

# Recall project-level understanding
recall_understanding(target="project")

# Recall from ACTUAL cached paths shown in stats output
# Common examples - use paths from YOUR get_understanding_stats output:
recall_understanding(target="{project_path}/auth")   # if exists in stats
recall_understanding(target="{project_path}/api")    # if exists in stats

# Use cached understanding to:
# - Identify config files related to analyzed modules
# - Understand config dependencies
# - Skip re-reading source files

# AFTER config analysis, store configuration understanding:
store_understanding(
  scope="module",
  target="{project_path}/config",
  purpose="Configuration layer managing app settings, secrets, and environment",
  importance="high",
  key_points=["<config file types>", "<env vars>", "<secrets management>"],
  gotchas=["<security concerns>", "<env-specific behaviors>"],
  analysis="<detailed_logic_and_flow_explanation>"
)
```

---

## Pre-Check: Verify Previous Substage

1. Verify `{data_dir}/deep-dive-patterns.json` exists
2. Load deep dive patterns

**IF not complete:** STOP - Return to 02b-deep-dive

---

## Step 1: Run Configuration Scan

Execute the deterministic config-scan CLI command:

```bash
speckitadv config-scan "{project_path}" --analysis-dir "{analysis_dir}"
```

This single command:

1. Finds all configuration files by pattern (JSON, YAML, TOML, env, ini, etc.)
2. Groups config files by pattern category
3. Searches for config-related code references

**Output:** `{data_dir}/config-analysis.json`

---

**[STOP: CONFIG_SCAN]**

Execute the command and verify output.

**IF successful:** config-analysis.json will be created
**IF fails:** Check civyk-repoix daemon status and retry

---

## Step 2: Read Discovery Results

Read the generated config scan results:

```bash
Read file: {data_dir}/config-analysis.json
```

Review the discovered configuration files:

- `config_files` - Configuration files grouped by pattern category
- `total_files` - Total count of config files found
- `config_references` - Code references mentioning config/settings
- `patterns_searched` - File patterns that were searched

---

## Step 3: Application Configuration

Based on discovery results, read application config files (select from `config_files`):

```text
# Check cache first
recall_understanding(target="{project_path}/{app_config_1}")
# IF not cached: Read file: {project_path}/{app_config_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{app_config_2}")
# IF not cached: Read file: {project_path}/{app_config_2}
# [!] NOW CALL store_understanding for the file above
```

---
**[STOP: ANALYZE_APP_CONFIG]**

Analyze all application configuration files (100% coverage):

**For each application config file, extract:**

1. **Database Settings:**
   - Connection URL/host/port
   - Database name
   - Credentials handling (referenced env var)
   - Connection pool settings
   - Timeout settings

2. **External Services:**
   - API endpoints
   - Service URLs
   - Timeout configurations
   - Retry settings

3. **Security Settings:**
   - JWT secrets/keys (note if hardcoded - SECURITY ISSUE)
   - Token expiration
   - CORS configuration
   - SSL/TLS settings

4. **Performance Settings:**
   - Thread pool sizes
   - Cache TTLs
   - Request timeouts
   - Rate limits

5. **Feature Flags:**
   - Toggle names
   - Default values
   - Environment overrides

**Output Format:**

```text
Application Configuration Analysis:

Profiles/Environments Detected: {list}

Database:
  Type: {PostgreSQL/MySQL/MongoDB/etc}
  Host: {env var reference or value}
  Connection Pool: min={n}, max={m}
  Timeout: {seconds}

External Services:
  {Service1}: {url} (timeout: {ms})
  {Service2}: {url} (timeout: {ms})

Security:
  JWT Secret: {env var | [!] HARDCODED}
  Token Expiry: {duration}
  CORS Origins: {list or pattern}

Performance:
  Thread Pool: {size}
  Cache TTL: {duration}
  Request Timeout: {duration}

```

---

## Step 4: Build Configuration

Read build configuration files (select from `config_files`):

```text
# Check cache first
recall_understanding(target="{project_path}/{build_config_1}")
# IF not cached: Read file: {project_path}/{build_config_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{build_config_2}")
# IF not cached: Read file: {project_path}/{build_config_2}
# [!] NOW CALL store_understanding for the file above
```

---
**[STOP: ANALYZE_BUILD_CONFIG]**

Analyze all build configuration files:

**Files to Check:**

- `pom.xml` (Maven)
- `build.gradle`, `build.gradle.kts` (Gradle)
- `package.json` (npm/yarn)
- `pyproject.toml`, `setup.py` (Python)
- `Cargo.toml` (Rust)
- `go.mod` (Go)
- `*.csproj`, `*.sln` (.NET)

**Extract:**

1. **Project Metadata:**
   - Name, version, description
   - Group/organization
   - Authors/maintainers

2. **Dependencies:**
   - Direct dependencies with versions
   - Dev dependencies
   - Plugin/extension dependencies

3. **Build Settings:**
   - Source/target version
   - Compiler options
   - Build profiles

4. **Scripts/Tasks:**
   - Build commands
   - Test commands
   - Deployment scripts

**Output Format:**

```text
Build Configuration Analysis:

Build Tool: {Maven/Gradle/npm/etc}
Project: {name} v{version}

Dependencies: {total_count}
  Runtime: {count}
  Dev/Test: {count}
  Plugins: {count}

Compilation Target: {Java 17 / Node 20 / etc}
Build Profiles: {list}

Scripts/Tasks:
  build: {command}
  test: {command}
  deploy: {command if exists}

```

---

## Step 5: Infrastructure Configuration

Read infrastructure configuration files (select from `config_files`):

```text
# Check cache first
recall_understanding(target="{project_path}/{infra_config_1}")
# IF not cached: Read file: {project_path}/{infra_config_1}
# [!] NOW CALL store_understanding for the file above

recall_understanding(target="{project_path}/{infra_config_2}")
# IF not cached: Read file: {project_path}/{infra_config_2}
# [!] NOW CALL store_understanding for the file above
```

---
**[STOP: ANALYZE_INFRA_CONFIG]**

Analyze all infrastructure/deployment configuration:

**Files to Check:**

- `Dockerfile`, `docker-compose.yml`
- `kubernetes/*.yaml`, `k8s/*.yaml`
- Helm charts
- Terraform files (`*.tf`)
- CloudFormation templates
- CI/CD configs (`.github/workflows`, `Jenkinsfile`, `.gitlab-ci.yml`)

**Extract:**

1. **Container Configuration:**
   - Base image
   - Exposed ports
   - Environment variables
   - Health checks
   - Resource limits

2. **Orchestration:**
   - Replicas/scaling
   - Load balancing
   - Service discovery
   - Secrets management

3. **CI/CD Pipeline:**
   - Pipeline stages
   - Build steps
   - Test steps
   - Deployment steps

**Output Format:**

```text
Infrastructure Configuration Analysis:

Container:
  Runtime: {Docker/Podman}
  Base Image: {image:tag}
  Exposed Ports: {list}
  Health Check: {yes/no}

Orchestration:
  Platform: {K8s/ECS/Docker Compose/None}
  Replicas: {default count}
  Scaling: {HPA/manual/none}

CI/CD:
  Platform: {GitHub Actions/Jenkins/GitLab/etc}
  Stages: {list}
  Deployment: {method}

```

---

## Step 6: Extract All Settings Summary

Merge CLI discovery with file reading insights into a comprehensive settings inventory:

```json
{
  "config_analysis": {
    "application": {
      "profiles": ["{list}"],
      "database": {
        "type": "{engine}",
        "host_source": "{env var name}",
        "pool_size": "{min-max}",
        "timeout_ms": {value}
      },
      "external_services": [
        {"name": "{service}", "url_source": "{env or value}", "timeout_ms": {value}}
      ],
      "security": {
        "jwt_secret_source": "{env var or HARDCODED}",
        "token_expiry_seconds": {value},
        "cors_origins": ["{list}"]
      },
      "performance": {
        "thread_pool_size": {value},
        "cache_ttl_seconds": {value},
        "request_timeout_ms": {value}
      },
      "feature_flags": [
        {"name": "{flag}", "default": "{value}", "description": "{purpose}"}
      ]
    },
    "build": {
      "tool": "{Maven/Gradle/npm/etc}",
      "project_name": "{name}",
      "project_version": "{version}",
      "target_runtime": "{Java 17/Node 20/etc}",
      "dependencies": {
        "runtime": {count},
        "dev": {count},
        "total": {count}
      }
    },
    "infrastructure": {
      "containerization": "{Docker/none}",
      "base_image": "{image:tag}",
      "orchestration": "{K8s/ECS/none}",
      "cicd_platform": "{GitHub Actions/Jenkins/none}"
    },
    "security_issues": [
      {"severity": "HIGH", "issue": "Hardcoded secret in {file}", "line": {n}}
    ],
    "files_analyzed": {count},
    "coverage": "100%"
  }
}

```

Save configuration analysis to `{data_dir}/config-analysis.json`:

```powershell
@"
<full config_analysis json here>
"@ | speckitadv write-data config-analysis.json --stage=02c-config-analysis --stdin
```

---

## Output Summary

```text
===========================================================
  SUBSTAGE COMPLETE: 02c-config-analysis (Phase 3)

  Time Used: 15% allocation

  Configuration Files Analyzed: {count}
  Coverage: 100%

  Key Findings:
    Profiles: {list}
    Database: {type}
    External Services: {count}
    CI/CD: {platform}

  Security Issues in Config: {count}

  Proceeding to Phase 4: Test & Dependency Audit
===========================================================

```

---

---

## Next Stage

**[AUTO-CONTINUE]** Run the CLI command below NOW. Do NOT generate content without the next stage prompt.

```bash
speckitadv analyze-project
```

The CLI auto-detects current stage and emits the next prompt. **Do NOT analyze or generate artifacts until you run this command.**
