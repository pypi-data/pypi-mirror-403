# sdlcctl - SDLC 5.0.0 Structure Validator CLI

**Version**: 1.1.0
**Framework**: SDLC 5.0.0
**Author**: SDLC Orchestrator Team

A command-line tool for validating, fixing, and initializing SDLC 5.0.0 compliant project structures.

---

## Features

- **Validate** project folder structure against SDLC 5.0.0 standards
- **Fix** missing stage folders and P0 artifacts automatically
- **Initialize** new projects with complete SDLC structure
- **Generate reports** in Markdown, JSON, or HTML formats
- **4-Tier Classification** support (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
- **Pre-commit hook** for CI/CD integration (<2s execution)
- **Rich CLI output** with colored tables and progress indicators

---

## Installation

### From PyPI (Recommended)

```bash
pip install sdlcctl
```

### From Source

```bash
git clone https://github.com/your-org/sdlc-orchestrator.git
cd sdlc-orchestrator/backend/sdlcctl
pip install -e .
```

### Dependencies

- Python 3.11+
- typer[all] >= 0.9.0
- click < 8.2 (required for Typer compatibility)
- rich >= 13.0.0

---

## Quick Start

### 1. Validate an existing project

```bash
# Validate current directory
sdlcctl validate

# Validate specific path
sdlcctl validate --path /path/to/project

# Validate with specific tier
sdlcctl validate --tier professional
```

### 2. Initialize a new project

```bash
# Interactive initialization
sdlcctl init

# Non-interactive with specific tier
sdlcctl init --tier professional --no-interactive
```

### 3. Fix issues automatically

```bash
# Preview fixes (dry-run)
sdlcctl fix --dry-run

# Apply fixes automatically
sdlcctl fix --no-interactive
```

---

## Commands

### `sdlcctl validate`

Validate SDLC 5.0.0 folder structure compliance.

```bash
sdlcctl validate [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Project root path | Current directory |
| `--docs` | `-d` | Documentation folder name | `docs` |
| `--tier` | `-t` | Project tier (lite/standard/professional/enterprise) | Auto-detect |
| `--team-size` | | Team size for auto-tier detection | None |
| `--format` | `-f` | Output format (text/json/github/summary) | `text` |
| `--output` | `-o` | Write output to a file | stdout |
| `--config` | `-c` | Path to `.sdlc-config.json` (default: auto-discover) | None |
| `--strict` | `-s` | Exit with error if any warnings/errors found | `false` |
| `--verbose` | `-v` | Show detailed output (includes context in text output) | `false` |

**Examples:**

```bash
# Basic validation
sdlcctl validate

# JSON output for CI/CD
sdlcctl validate --format json

# Strict mode (fail on warnings)
sdlcctl validate --strict

# Auto-detect tier from team size
sdlcctl validate --team-size 25

# GitHub Actions annotations
sdlcctl validate --format github --strict

# Write JSON output to file
sdlcctl validate --format json --output report.json

# Enforce required stages for a tier
sdlcctl validate --tier professional
```

**Exit Codes:**
- `0` - Compliant (no errors)
- `1` - Non-compliant (errors found or strict mode with warnings)

---

### `sdlcctl fix`

Automatically fix SDLC structure issues.

```bash
sdlcctl fix [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Project root path | Current directory |
| `--docs` | `-d` | Documentation folder name | `docs` |
| `--tier` | `-t` | Project tier | Auto-detect |
| `--dry-run` | | Preview changes without applying | `false` |
| `--interactive` | `-i` | Prompt before each fix | `true` |
| `--no-interactive` | | Do not prompt before each fix | `false` |
| `--stages` | | Fix missing stage folders | `true` |
| `--no-stages` | | Do not fix missing stage folders | `false` |
| `--p0` | | Generate missing P0 artifacts | `true` |
| `--no-p0` | | Do not generate missing P0 artifacts | `false` |
| `--naming` | | Fix naming violations | `false` |
| `--no-naming` | | Do not fix naming violations | `false` |

**Notes:**
- A conservative Sprint 44 scanner auto-fix runs first (when `docs/` exists):
  - Create missing required stages (when `--tier` is provided)
  - Rename stage folders for `STAGE-001` / `STAGE-003`
  - Fix invalid numbering prefixes for `NUM-003`
- The legacy fix flow then runs (missing stages, optional P0 generation, etc.)

**Examples:**

```bash
# Preview what would be fixed
sdlcctl fix --dry-run

# Fix automatically without prompts
sdlcctl fix --no-interactive

# Fix only stages (not P0 artifacts)
sdlcctl fix --stages --no-p0
```

---

### `sdlcctl init`

Initialize SDLC 5.0.0 project structure.

```bash
sdlcctl init [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Project root path | Current directory |
| `--docs` | `-d` | Documentation folder name | `docs` |
| `--tier` | `-t` | Project tier | Interactive prompt |
| `--team-size` | | Team size for auto-tier | None |
| `--scaffold` | | Create full folder structure | `true` |
| `--no-scaffold` | | Do not create READMEs and templates | `false` |
| `--force` | `-f` | Overwrite existing docs | `false` |
| `--interactive` | `-i` | Interactive mode | `true` |
| `--no-interactive` | | Do not prompt; use defaults where needed | `false` |

**Examples:**

```bash
# Interactive initialization
sdlcctl init

# Initialize for a 25-person team
sdlcctl init --team-size 25

# Non-interactive enterprise setup
sdlcctl init --tier enterprise --no-interactive --force
```

---

### `sdlcctl report`

Generate SDLC compliance reports.

```bash
sdlcctl report [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Project root path | Current directory |
| `--docs` | `-d` | Documentation folder name | `docs` |
| `--tier` | `-t` | Project tier | Auto-detect |
| `--format` | `-f` | Output format (markdown/json/html) | `markdown` |
| `--output` | `-o` | Output file path | stdout |

**Examples:**

```bash
# Generate Markdown report
sdlcctl report --format markdown --output COMPLIANCE.md

# Generate HTML report
sdlcctl report --format html --output report.html

# JSON report to stdout
sdlcctl report --format json
```

---

### `sdlcctl tiers`

Display tier classification details.

```bash
sdlcctl tiers
```

**Output:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SDLC 5.0.0 Tier Classification                    │
├─────────────────┬──────────────┬──────────┬────────────┬────────────────┤
│ Tier            │    Team Size │   Stages │ P0 Required│ Compliance     │
├─────────────────┼──────────────┼──────────┼────────────┼────────────────┤
│ LITE            │          1-2 │        4 │     ❌     │ -              │
│ STANDARD        │         3-10 │        6 │     ❌     │ -              │
│ PROFESSIONAL    │        10-50 │       10 │     ✅     │ ISO 27001      │
│ ENTERPRISE      │          50+ │       11 │     ✅     │ SOC 2, HIPAA   │
└─────────────────┴──────────────┴──────────┴────────────┴────────────────┘
```

---

### `sdlcctl stages`

Display SDLC 5.0.0 stage definitions.

```bash
sdlcctl stages
```

**Output:**
```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              SDLC 5.0.0 Stages                                 │
├──────┬─────────────────────────────────┬───────────────────────────────────────┤
│ ID   │ Stage Name                      │ Question                              │
├──────┼─────────────────────────────────┼───────────────────────────────────────┤
│ 00   │ 00-Project-Foundation           │ WHY does this project exist?          │
│ 01   │ 01-Planning-Analysis            │ WHAT needs to be built?               │
│ 02   │ 02-Design-Architecture          │ HOW will it be built?                 │
│ 03   │ 03-Development-Implementation   │ BUILD - How to implement?             │
│ 04   │ 04-Testing-QA                   │ TEST - How to verify quality?         │
│ 05   │ 05-Deployment-Release           │ DEPLOY - How to release?              │
│ 06   │ 06-Operations-Monitoring        │ OPERATE - How to run in production?   │
│ 07   │ 07-Integration-External         │ INTEGRATE - How to connect systems?   │
│ 08   │ 08-Collaboration-Team           │ COLLABORATE - How do teams work?      │
│ 09   │ 09-Executive-Reports            │ GOVERN - How to manage & report?      │
│ 10   │ 10-Archive-Lessons              │ ARCHIVE - How to preserve history?    │
└──────┴─────────────────────────────────┴───────────────────────────────────────┘
```

---

### `sdlcctl p0`

Display P0 artifact requirements.

```bash
sdlcctl p0
```

Shows all 15 P0 artifacts with tier requirements:
- Vision Document
- Problem Statement
- Business Requirements
- Functional Requirements
- Technical Design
- Sprint Plans
- And more...

---

## Tier Classification

SDLC 5.0.0 supports 4 tiers based on team size and compliance needs:

| Tier | Team Size | Required Stages | P0 Artifacts | Compliance |
|------|-----------|-----------------|--------------|------------|
| **LITE** | 1-2 | 4 (00-03) | Optional | None |
| **STANDARD** | 3-10 | 6 (00-05) | Optional | None |
| **PROFESSIONAL** | 10-50 | 10 (00-09) | Required | ISO 27001 |
| **ENTERPRISE** | 50+ | 11 (00-10) | Required | SOC 2, HIPAA |

### Auto-Detection

```bash
# Detect tier from team size
sdlcctl validate --team-size 25  # → PROFESSIONAL

# Explicit tier
sdlcctl validate --tier enterprise
```

---

## Configuration (.sdlc-config.json)

sdlcctl supports project-specific configuration via `.sdlc-config.json`. Place this file in your project root or docs folder.

### Minimal Configuration

```json
{
  "tier": "professional",
  "docs_root": "docs"
}
```

### Full Configuration Example

```json
{
  "$schema": "https://sdlc-orchestrator.com/schemas/config-v1.json",
  "validators": [
    "stage-folder",
    "sequential-numbering",
    "naming-convention",
    "header-metadata",
    "cross-reference"
  ],
  "rules": {
    "STAGE-001": { "enabled": true, "severity": "ERROR", "auto_fix": true },
    "STAGE-002": { "enabled": true, "severity": "ERROR" },
    "STAGE-003": { "enabled": true, "severity": "WARNING", "auto_fix": true },
    "STAGE-005": { "enabled": true, "severity": "ERROR" },
    "NUM-001": { "enabled": true, "severity": "ERROR" },
    "NUM-002": { "enabled": true, "severity": "INFO", "auto_fix": true },
    "NUM-003": { "enabled": true, "severity": "WARNING", "auto_fix": true },
    "NAME-001": { "enabled": true, "severity": "WARNING", "auto_fix": true },
    "NAME-002": { "enabled": true, "severity": "INFO" },
    "HDR-001": { "enabled": true, "severity": "WARNING" },
    "HDR-002": { "enabled": true, "severity": "INFO" },
    "REF-001": { "enabled": true, "severity": "ERROR" },
    "REF-002": { "enabled": true, "severity": "WARNING" }
  },
  "ignore_patterns": [
    "**/node_modules/**",
    "**/.git/**",
    "**/__pycache__/**",
    "**/10-archive/**",
    "**/99-legacy/**"
  ],
  "max_workers": 4,
  "docs_root": "docs",
  "fail_on_error": true,
  "fail_on_warning": false,
  "output_format": "text"
}
```

### Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `validators` | string[] | List of validators to run | All 5 validators |
| `rules` | object | Per-rule overrides | See below |
| `ignore_patterns` | string[] | Glob patterns to skip | node_modules, .git, etc. |
| `max_workers` | int | Parallel validation threads | 4 |
| `docs_root` | string | Documentation folder name | "docs" |
| `fail_on_error` | bool | Exit code 1 on errors | true |
| `fail_on_warning` | bool | Exit code 1 on warnings | false |
| `output_format` | string | Default output format | "text" |

### Per-Rule Configuration

Each rule can be configured with:

```json
{
  "RULE-ID": {
    "enabled": true,      // Enable/disable this rule
    "severity": "ERROR",  // Override severity: ERROR, WARNING, INFO
    "auto_fix": true,     // Allow auto-fix for this rule
    "options": {}         // Rule-specific options
  }
}
```

### Example: Disable Orphaned File Warnings

```json
{
  "rules": {
    "REF-002": { "enabled": false }
  }
}
```

### Example: Strict Mode (All Warnings → Errors)

```json
{
  "rules": {
    "STAGE-003": { "severity": "ERROR" },
    "NAME-001": { "severity": "ERROR" },
    "NUM-002": { "severity": "ERROR" }
  },
  "fail_on_warning": true
}
```

### Example: Lite Tier (Minimal Validation)

```json
{
  "validators": ["stage-folder"],
  "rules": {
    "STAGE-005": { "enabled": false }
  },
  "ignore_patterns": ["**/99-legacy/**", "**/10-archive/**"]
}
```

---

## Pre-commit Hook Integration

### Setup with pre-commit framework

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: sdlcctl-validate
        name: SDLC 5.0.0 Validation
        entry: python -m sdlcctl.hooks.pre_commit
        language: python
        pass_filenames: false
        always_run: true
        stages: [commit]
```

### Manual Hook Setup

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
python -m sdlcctl.hooks.pre_commit --tier professional
exit $?
```

### Hook Options

```bash
python -m sdlcctl.hooks.pre_commit [OPTIONS]

Options:
  --path, -p      Project root path
  --docs, -d      Documentation folder name (default: docs)
  --tier, -t      Project tier
  --strict, -s    Fail on warnings
```

### Performance

- Target: <2 seconds execution time
- Optimized for incremental validation
- Caches folder structure scans

---

## CI/CD Integration

### GitHub Actions

```yaml
name: SDLC Compliance

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install sdlcctl
        run: pip install sdlcctl

      - name: Validate SDLC Structure
        run: sdlcctl validate --tier professional --format summary

      - name: Generate Report
        if: always()
        run: sdlcctl report --format markdown --output COMPLIANCE.md

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: compliance-report
          path: COMPLIANCE.md
```

### GitLab CI

```yaml
sdlc-validation:
  stage: lint
  image: python:3.11
  script:
    - pip install sdlcctl
    - sdlcctl validate --tier professional --strict
  artifacts:
    reports:
      dotenv: compliance.env
```

---

## P0 Artifacts

P0 (Priority Zero) artifacts are essential documents that AI assistants use for project context. They provide:

1. **Navigation** - Entry points for each stage
2. **Context** - Project vision, requirements, architecture
3. **Traceability** - Links between artifacts

### Required P0 Artifacts (Professional/Enterprise)

| Artifact | Stage | Path |
|----------|-------|------|
| Vision Document | 00 | `docs/00-Project-Foundation/01-Vision/Product-Vision.md` |
| Problem Statement | 00 | `docs/00-Project-Foundation/03-Design-Thinking/Problem-Statement.md` |
| Product Roadmap | 00 | `docs/00-Project-Foundation/04-Roadmap/Product-Roadmap.md` |
| Functional Requirements | 01 | `docs/01-Planning-Analysis/01-Requirements/Functional-Requirements-Document.md` |
| System Architecture | 02 | `docs/02-Design-Architecture/01-System-Architecture/System-Architecture-Document.md` |
| Technical Design | 02 | `docs/02-Design-Architecture/Technical-Design-Document.md` |
| API Specification | 02 | `docs/02-Design-Architecture/03-API-Design/openapi.yml` |
| Sprint Plans | 03 | `docs/03-Development-Implementation/02-Sprint-Plans/` |
| And more... | | |

Run `sdlcctl p0` to see all 15 artifacts with tier requirements.

---

## Folder Structure

SDLC 5.0.0 compliant project structure:

```
project/
├── docs/
│   ├── README.md                           # Main docs entry point
│   ├── 00-Project-Foundation/
│   │   ├── README.md                       # Stage entry point
│   │   ├── 01-Vision/
│   │   ├── 02-Business-Case/
│   │   ├── 03-Design-Thinking/
│   │   ├── 04-Roadmap/
│   │   └── 99-Legacy/                      # AI: DO NOT READ
│   ├── 01-Planning-Analysis/
│   │   ├── README.md
│   │   ├── 01-Requirements/
│   │   ├── 02-User-Stories/
│   │   └── 99-Legacy/
│   ├── 02-Design-Architecture/
│   │   ├── README.md
│   │   ├── 01-System-Architecture/
│   │   ├── 02-Data-Model/
│   │   ├── 03-API-Design/
│   │   ├── 04-ADRs/
│   │   └── 99-Legacy/
│   ├── 03-Development-Implementation/
│   ├── 04-Testing-QA/
│   ├── 05-Deployment-Release/
│   ├── 06-Operations-Monitoring/
│   ├── 07-Integration-External/
│   ├── 08-Collaboration-Team/
│   ├── 09-Executive-Reports/
│   └── 10-Archive-Lessons/                 # ENTERPRISE only
└── src/
```

### 99-Legacy Folders

Each stage includes a `99-Legacy/` folder for archived content:

```markdown
# Legacy Content

**AI Directive**: DO NOT READ this folder.

This folder contains archived, outdated content.
Move deprecated documents here instead of deleting them.
```

---

## Validation Rules

### Stage Validation (STAGE-xxx)

| Code | Severity | Description |
|------|----------|-------------|
| STAGE-001 | ERROR | Missing required stage folder |
| STAGE-002 | ERROR | Stage folder missing README.md |
| STAGE-003 | WARNING | Stage naming convention violation |
| STAGE-004 | INFO | Optional stage not present |

### P0 Validation (P0-xxx)

| Code | Severity | Description |
|------|----------|-------------|
| P0-001 | ERROR | Missing required P0 artifact |
| P0-002 | WARNING | P0 artifact below minimum content |
| P0-003 | WARNING | P0 artifact missing required sections |

### Naming Validation (NAME-xxx)

| Code | Severity | Description |
|------|----------|-------------|
| NAME-001 | WARNING | Stage folder naming mismatch |
| NAME-002 | INFO | Subfolder naming suggestion |

---

## Programmatic Usage

Use sdlcctl as a Python library:

```python
from sdlcctl import SDLCValidator, Tier

# Initialize validator
validator = SDLCValidator(
    project_root="/path/to/project",
    docs_root="docs",
    tier=Tier.PROFESSIONAL,
)

# Run validation
result = validator.validate()

# Check results
print(f"Compliant: {result.is_compliant}")
print(f"Score: {result.compliance_score}/100")
print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")

# Iterate issues
for issue in result.issues:
    print(f"[{issue.severity}] {issue.code}: {issue.message}")

# Export as dict
data = result.to_dict()
```

---

## Development

### Running Tests

```bash
cd backend/sdlcctl
pytest tests/ -v --cov=sdlcctl --cov-report=term-missing
```

### Test Coverage Target

- **Minimum**: 95%+ coverage
- **Current**: 95.05% (207 tests)

### Linting

```bash
ruff check .
mypy . --strict
```

---

## Troubleshooting

### Common Issues

**1. "No docs folder found"**
```bash
# Solution: Specify custom docs folder
sdlcctl validate --docs documentation
```

**2. "Invalid tier"**
```bash
# Valid options: lite, standard, professional, enterprise
sdlcctl validate --tier professional
```

**3. Pre-commit hook too slow**
```bash
# Check performance
time python -m sdlcctl.hooks.pre_commit

# Target: <2 seconds
```

**4. Permission denied on fix**
```bash
# Check folder permissions
ls -la docs/

# Use sudo if needed (not recommended)
sudo sdlcctl fix --no-interactive
```

---

## License

Apache-2.0

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure tests pass with 95%+ coverage
4. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed guidelines.

---

## Links

- **Documentation**: [SDLC 5.0.0 Framework](https://github.com/your-org/sdlc-framework)
- **Issues**: [GitHub Issues](https://github.com/your-org/sdlc-orchestrator/issues)
- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)

---

*Generated by SDLC Orchestrator Team - Sprint 29*
