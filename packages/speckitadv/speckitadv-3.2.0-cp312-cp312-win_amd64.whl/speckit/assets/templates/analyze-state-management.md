# State Management

The CLI provides all context via template variables. **Do not read state.json directly.**

**Available template variables:**

- `{project_path}` - Project being analyzed
- `{analysis_dir}` - Analysis folder path (root)
- `{data_dir}` - Data folder for JSON files (`{analysis_dir}/data/`)
- `{reports_dir}` - Reports folder for MD files (`{analysis_dir}/reports/`)
- `{scope}` - Analysis scope (A or B)
- `{context}` - Additional context
- `{concern_type}`, `{current_impl}`, `{target_impl}` - Scope B specific

**CLI Utility Commands:**

[!] **OS command line length limits apply (~8000 chars on Windows).**

**IMPORTANT:** Chunking means MULTIPLE write operations, NOT reduced content. Generate FULL comprehensive output.

```bash
# Write JSON data
speckitadv write-data <filename> --stage=<stage-id> --content '<json>'

# Write report - ALWAYS use --append (creates if not exists, appends if exists)
speckitadv write-report <filename> --stage=<stage-id> --append --content '<content>'

# Get file statistics
speckitadv file-stats <filepath>
```

**For content > 2000 chars, use stdin mode:**

```powershell
@"
<content here>
"@ | speckitadv write-data <filename> --stage=<stage-id> --stdin
```
