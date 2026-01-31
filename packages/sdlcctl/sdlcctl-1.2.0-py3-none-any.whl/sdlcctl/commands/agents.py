"""
=========================================================================
SDLC 6.0.0 AGENTS.md Commands
SDLC Orchestrator - Sprint 80/81/103

Version: 1.2.0
Date: January 23, 2026
Status: ACTIVE - Sprint 103 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-029-AGENTS-MD-Integration-Strategy

Purpose:
- Generate AGENTS.md from project analysis
- Validate AGENTS.md content
- Lint and auto-fix AGENTS.md
- Fetch dynamic context overlay (Sprint 81)
- Validate per-file context limits <60 lines (Sprint 103)

Commands:
    sdlcctl agents init             - Generate AGENTS.md
    sdlcctl agents validate         - Validate existing AGENTS.md
    sdlcctl agents lint             - Lint and auto-fix
    sdlcctl agents context          - Fetch current SDLC context overlay (Sprint 81)
    sdlcctl agents validate-context - Validate per-file context <60 lines (Sprint 103)
=========================================================================
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table
from rich.syntax import Syntax

console = Console()


# ============================================================================
# Secret Detection Patterns
# ============================================================================

SECRET_PATTERNS: List[Tuple[str, str]] = [
    (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub PAT"),
    (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth token"),
    (r'ghs_[a-zA-Z0-9]{36}', "GitHub App token"),
    (r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', "GitHub Fine-grained PAT"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'[a-zA-Z0-9/+=]{40}', "AWS Secret Key (potential)"),
    (r'sk_live_[a-zA-Z0-9]{24,}', "Stripe Live Key"),
    (r'sk_test_[a-zA-Z0-9]{24,}', "Stripe Test Key"),
    (r'xox[baprs]-[0-9a-zA-Z-]{10,}', "Slack Token"),
    (r'sk-ant-api[a-zA-Z0-9-]{20,}', "Anthropic API Key"),
    (r'://[^:]+:[^@]+@', "URL with credentials"),
    (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', "JWT Token"),
]

# Patterns to ignore (placeholders, examples)
IGNORE_PATTERNS: List[str] = [
    r'your[_-]?key[_-]?here',
    r'<your[_-]?token>',
    r'example',
    r'placeholder',
    r'data:image/',  # Base64 images
]


# ============================================================================
# Utility Functions
# ============================================================================

def detect_secrets(content: str) -> List[dict]:
    """Detect secrets in content."""
    issues = []

    for line_num, line in enumerate(content.split('\n'), start=1):
        # Skip if line matches ignore patterns
        if any(re.search(p, line, re.IGNORECASE) for p in IGNORE_PATTERNS):
            continue

        for pattern, description in SECRET_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                # Double-check it's not a placeholder
                matched_text = match.group()
                if any(re.search(p, matched_text, re.IGNORECASE) for p in IGNORE_PATTERNS):
                    continue

                issues.append({
                    "line": line_num,
                    "column": match.start(),
                    "type": "error",
                    "code": "SECRET_DETECTED",
                    "message": f"{description} detected",
                    "snippet": line[:80] + "..." if len(line) > 80 else line,
                })

    return issues


def count_lines(content: str) -> int:
    """Count lines in content."""
    return len(content.strip().split('\n'))


def validate_structure(content: str) -> List[dict]:
    """Validate AGENTS.md structure."""
    issues = []
    lines = content.strip().split('\n')

    # Check for header
    if not lines or not lines[0].startswith('# '):
        issues.append({
            "line": 1,
            "type": "warning",
            "code": "MISSING_HEADER",
            "message": "AGENTS.md should start with '# AGENTS.md - <project name>'",
        })

    # Check line limit
    line_count = len(lines)
    if line_count > 200:
        issues.append({
            "line": line_count,
            "type": "error",
            "code": "EXCEEDS_MAX_LINES",
            "message": f"Content exceeds maximum 200 lines ({line_count} lines)",
        })
    elif line_count > 150:
        issues.append({
            "line": line_count,
            "type": "warning",
            "code": "OVER_RECOMMENDED",
            "message": f"Content over recommended 150 lines ({line_count} lines)",
        })

    # Check for recommended sections
    recommended_sections = ["Quick Start", "Architecture", "DO NOT"]
    content_lower = content.lower()
    for section in recommended_sections:
        if section.lower() not in content_lower:
            issues.append({
                "line": 1,
                "type": "warning",
                "code": "MISSING_SECTION",
                "message": f"Recommended section '{section}' not found",
            })

    return issues


def lint_content(content: str) -> Tuple[str, List[str]]:
    """Lint and fix content."""
    changes = []
    lines = content.split('\n')
    fixed_lines = []

    prev_blank = False
    for i, line in enumerate(lines):
        # Remove trailing whitespace
        stripped = line.rstrip()
        if stripped != line:
            changes.append(f"Line {i+1}: Removed trailing whitespace")
            line = stripped

        # Collapse multiple blank lines
        is_blank = len(line.strip()) == 0
        if is_blank and prev_blank:
            changes.append(f"Line {i+1}: Removed extra blank line")
            continue

        fixed_lines.append(line)
        prev_blank = is_blank

    # Ensure single newline at end
    fixed_content = '\n'.join(fixed_lines)
    if not fixed_content.endswith('\n'):
        fixed_content += '\n'
        changes.append("Added newline at end of file")

    return fixed_content, changes


def analyze_project(project_path: Path) -> dict:
    """Analyze project structure for AGENTS.md generation."""
    analysis = {
        "name": project_path.name,
        "has_docker_compose": False,
        "docker_services": [],
        "has_package_json": False,
        "has_requirements": False,
        "has_poetry": False,
        "backend_type": None,
        "frontend_type": None,
        "has_tsconfig": False,
        "has_ruff": False,
        "has_eslint": False,
        "has_prettier": False,
        "has_minio": False,
        "has_grafana": False,
        "has_github_actions": False,
        "has_docs": False,
        "has_readme": False,
        "database_type": None,
        "quick_start_commands": [],
    }

    # Check docker-compose
    for compose_file in ["docker-compose.yml", "docker-compose.yaml"]:
        compose_path = project_path / compose_file
        if compose_path.exists():
            analysis["has_docker_compose"] = True
            try:
                content = compose_path.read_text()
                # Extract services
                import yaml
                try:
                    data = yaml.safe_load(content)
                    if data and "services" in data:
                        analysis["docker_services"] = list(data["services"].keys())

                        # Detect databases and AGPL
                        for service, config in data["services"].items():
                            image = config.get("image", "")
                            if "postgres" in image.lower():
                                analysis["database_type"] = "postgresql"
                            elif "mysql" in image.lower():
                                analysis["database_type"] = "mysql"
                            elif "mongo" in image.lower():
                                analysis["database_type"] = "mongodb"
                            elif "minio" in image.lower():
                                analysis["has_minio"] = True
                            elif "grafana" in image.lower():
                                analysis["has_grafana"] = True
                except:
                    pass

                analysis["quick_start_commands"].append("docker compose up -d")
            except:
                pass
            break

    # Check package.json (frontend)
    for pkg_path in [project_path / "package.json", project_path / "frontend" / "package.json"]:
        if pkg_path.exists():
            analysis["has_package_json"] = True
            try:
                data = json.loads(pkg_path.read_text())
                deps = data.get("dependencies", {})
                if "react" in deps:
                    if "next" in deps:
                        analysis["frontend_type"] = "nextjs"
                    else:
                        analysis["frontend_type"] = "react"
                elif "vue" in deps:
                    analysis["frontend_type"] = "vue"
                elif "@angular/core" in deps:
                    analysis["frontend_type"] = "angular"

                # Quick start from scripts
                scripts = data.get("scripts", {})
                if "dev" in scripts:
                    analysis["quick_start_commands"].append("npm run dev")
                elif "start" in scripts:
                    analysis["quick_start_commands"].append("npm start")
            except:
                pass
            break

    # Check requirements.txt / pyproject.toml
    if (project_path / "requirements.txt").exists() or (project_path / "backend" / "requirements.txt").exists():
        analysis["has_requirements"] = True
        analysis["backend_type"] = "python"

    if (project_path / "pyproject.toml").exists():
        analysis["has_poetry"] = True
        analysis["backend_type"] = "python"

    # Config files
    analysis["has_tsconfig"] = (project_path / "tsconfig.json").exists()
    analysis["has_ruff"] = (project_path / "ruff.toml").exists() or (project_path / "pyproject.toml").exists()
    analysis["has_eslint"] = any((project_path / f).exists() for f in [".eslintrc.json", ".eslintrc.js", ".eslintrc"])
    analysis["has_prettier"] = any((project_path / f).exists() for f in [".prettierrc", ".prettierrc.json", "prettier.config.js"])

    # CI/CD
    analysis["has_github_actions"] = (project_path / ".github" / "workflows").exists()

    # Docs
    analysis["has_docs"] = (project_path / "docs").exists()
    analysis["has_readme"] = (project_path / "README.md").exists()

    return analysis


def generate_agents_md(analysis: dict, max_lines: int = 150) -> str:
    """Generate AGENTS.md content from analysis."""
    sections = []

    # Header
    sections.append(f"# AGENTS.md - {analysis['name']}\n")
    sections.append("This file provides context for AI coding assistants (Cursor, Claude Code, Copilot).\n")
    sections.append("Keep ≤150 lines. Dynamic context is delivered via PR comments.\n")

    # Quick Start
    sections.append("## Quick Start\n")
    if analysis["quick_start_commands"]:
        for cmd in analysis["quick_start_commands"][:3]:
            sections.append(f"- `{cmd}`")
    else:
        sections.append("- `docker compose up -d` (if using Docker)")
        sections.append("- Check README.md for setup instructions")
    sections.append("")

    # Architecture
    sections.append("## Architecture\n")
    if analysis["backend_type"]:
        sections.append(f"- **Backend**: {analysis['backend_type'].title()}")
    if analysis["frontend_type"]:
        sections.append(f"- **Frontend**: {analysis['frontend_type'].title()}")
    if analysis["database_type"]:
        sections.append(f"- **Database**: {analysis['database_type'].title()}")
    if analysis["docker_services"]:
        sections.append(f"- **Services**: {', '.join(analysis['docker_services'][:5])}")
    sections.append("")

    # Current Stage
    sections.append("## Current Stage\n")
    sections.append("_Note: Current sprint/stage context is delivered dynamically via PR comments._")
    sections.append("_This section provides static defaults only._\n")
    sections.append("- Check `.sdlc-config.json` for SDLC tier and stage mapping")
    sections.append("- Check PR description for active sprint goals")
    sections.append("")

    # Conventions
    sections.append("## Conventions\n")
    if analysis["backend_type"] == "python":
        sections.append("**Python:**")
        sections.append("- snake_case for files and functions")
        sections.append("- Type hints required (Python 3.11+)")
        if analysis["has_ruff"]:
            sections.append("- Linting: ruff (see ruff.toml)")
        sections.append("")

    if analysis["frontend_type"]:
        sections.append("**Frontend:**")
        sections.append("- PascalCase for React components")
        sections.append("- camelCase for utilities")
        if analysis["has_tsconfig"]:
            sections.append("- TypeScript strict mode enabled")
        if analysis["has_eslint"]:
            sections.append("- ESLint for code quality")
        if analysis["has_prettier"]:
            sections.append("- Prettier for formatting")
        sections.append("")

    # Security
    sections.append("## Security\n")
    sections.append("- **NEVER** commit secrets (API keys, passwords)")
    sections.append("- Use environment variables for configuration")
    if analysis["has_minio"] or analysis["has_grafana"]:
        sections.append("- **AGPL Containment**: Network-only access to AGPL components")
        if analysis["has_minio"]:
            sections.append("  - MinIO: Use S3 API via HTTP (no SDK import)")
        if analysis["has_grafana"]:
            sections.append("  - Grafana: Embed via iframe only")
    sections.append("- Follow OWASP Top 10 guidelines")
    sections.append("")

    # Git Workflow
    sections.append("## Git Workflow\n")
    sections.append("- **Branch naming**: `feature/`, `fix/`, `chore/`")
    sections.append("- **Commit format**: `type(scope): description`")
    sections.append("- **PR required**: All changes via Pull Request")
    if analysis["has_github_actions"]:
        sections.append("- **CI/CD**: GitHub Actions (lint, test, build)")
    sections.append("")

    # DO NOT
    sections.append("## DO NOT\n")
    sections.append("- Add TODO comments or placeholder code (Zero Mock Policy)")
    sections.append("- Skip error handling")
    sections.append("- Hardcode secrets or environment-specific values")
    sections.append("- Import AGPL libraries directly (use network APIs)")
    sections.append("- Commit without running tests")
    sections.append("- Push directly to main branch")
    sections.append("")

    # Footer
    sections.append("---\n")
    sections.append(f"_Generated by sdlcctl agents init | {datetime.now().strftime('%Y-%m-%d')}_")

    content = '\n'.join(sections)

    # Truncate if over limit
    lines = content.split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines-2]
        lines.append("")
        lines.append(f"_[Truncated to {max_lines} lines]_")
        content = '\n'.join(lines)

    return content


# ============================================================================
# CLI Commands
# ============================================================================

def agents_init_command(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: AGENTS.md in project root)",
    ),
    max_lines: int = typer.Option(
        150,
        "--max-lines",
        "-m",
        help="Maximum lines (50-200)",
        min=50,
        max=200,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing AGENTS.md",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print content without writing file",
    ),
) -> None:
    """
    Generate AGENTS.md from project analysis.

    Analyzes project structure (docker-compose, package.json, etc.)
    and generates a compliant AGENTS.md file.

    Examples:

        sdlcctl agents init

        sdlcctl agents init --max-lines 100

        sdlcctl agents init --dry-run
    """
    console.print()
    console.print(
        Panel(
            "[bold]AGENTS.md Generator[/bold]\n\n"
            "Generates AGENTS.md from project analysis.\n"
            "Follows ADR-029 two-layer architecture.",
            title="[bold blue]sdlcctl agents init[/bold blue]",
            border_style="blue",
        )
    )

    # Determine output path
    output_path = output or (path / "AGENTS.md")

    # Check if file exists
    if output_path.exists() and not force and not dry_run:
        if not Confirm.ask(f"[yellow]Warning:[/yellow] {output_path} exists. Overwrite?"):
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Analyze project
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing project...", total=None)
        analysis = analyze_project(path)
        progress.update(task, description="Analysis complete")

    # Show analysis summary
    console.print()
    table = Table(title="Project Analysis", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Project", analysis["name"])
    table.add_row("Backend", analysis["backend_type"] or "Not detected")
    table.add_row("Frontend", analysis["frontend_type"] or "Not detected")
    table.add_row("Database", analysis["database_type"] or "Not detected")
    table.add_row("Docker Compose", "✅" if analysis["has_docker_compose"] else "❌")
    table.add_row("AGPL Dependencies", "⚠️ Yes" if (analysis["has_minio"] or analysis["has_grafana"]) else "No")

    console.print(table)

    # Generate content
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating AGENTS.md...", total=None)
        content = generate_agents_md(analysis, max_lines)
        progress.update(task, description="Generation complete")

    # Validate generated content
    secrets = detect_secrets(content)
    if secrets:
        console.print()
        console.print("[bold red]ERROR: Secrets detected in generated content![/bold red]")
        for issue in secrets:
            console.print(f"  Line {issue['line']}: {issue['message']}")
        raise typer.Exit(code=1)

    # Show or write
    line_count = count_lines(content)
    console.print()

    if dry_run:
        console.print("[bold]Generated content:[/bold]")
        console.print()
        console.print(Syntax(content, "markdown", theme="monokai"))
    else:
        output_path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]✓ Generated AGENTS.md[/bold green]")
        console.print(f"  Path: {output_path}")

    console.print(f"  Lines: {line_count}/{max_lines}")
    console.print()

    # Next steps
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Review and customize the generated content")
    console.print("  2. Run 'sdlcctl agents validate' to check compliance")
    console.print("  3. Commit AGENTS.md to your repository")
    console.print()


def agents_validate_command(
    path: Path = typer.Argument(
        ...,
        help="Path to AGENTS.md file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Treat warnings as errors",
    ),
) -> None:
    """
    Validate AGENTS.md content.

    Checks for:
    - Secrets (API keys, tokens, passwords)
    - Line limits (150 recommended, 200 max)
    - Required sections
    - Markdown structure

    Examples:

        sdlcctl agents validate AGENTS.md

        sdlcctl agents validate AGENTS.md --strict
    """
    console.print()
    console.print(f"[bold]Validating:[/bold] {path}")
    console.print()

    # Read content
    content = path.read_text(encoding="utf-8")
    line_count = count_lines(content)

    # Run validations
    all_issues = []

    # Secret detection
    secrets = detect_secrets(content)
    all_issues.extend(secrets)

    # Structure validation
    structure_issues = validate_structure(content)
    all_issues.extend(structure_issues)

    # Separate errors and warnings
    errors = [i for i in all_issues if i.get("type") == "error"]
    warnings = [i for i in all_issues if i.get("type") == "warning"]

    # Display results
    if errors:
        console.print("[bold red]Errors:[/bold red]")
        for issue in errors:
            console.print(f"  Line {issue.get('line', '?')}: {issue['message']}")
        console.print()

    if warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for issue in warnings:
            console.print(f"  Line {issue.get('line', '?')}: {issue['message']}")
        console.print()

    # Summary
    console.print("[bold]Summary:[/bold]")
    console.print(f"  📊 Lines: {line_count}/150 (max 200)")
    console.print(f"  ❌ Errors: {len(errors)}")
    console.print(f"  ⚠️  Warnings: {len(warnings)}")
    console.print()

    # Exit code
    if errors or (strict and warnings):
        console.print("[bold red]✗ Validation FAILED[/bold red]")
        raise typer.Exit(code=1)
    elif warnings:
        console.print("[bold yellow]⚠ Validation PASSED with warnings[/bold yellow]")
    else:
        console.print("[bold green]✓ Validation PASSED[/bold green]")


def agents_lint_command(
    path: Path = typer.Argument(
        ...,
        help="Path to AGENTS.md file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Apply fixes to file",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show fixes without applying",
    ),
) -> None:
    """
    Lint and auto-fix AGENTS.md.

    Fixes:
    - Trailing whitespace
    - Multiple blank lines
    - Missing newline at end

    Examples:

        sdlcctl agents lint AGENTS.md

        sdlcctl agents lint AGENTS.md --fix

        sdlcctl agents lint AGENTS.md --dry-run
    """
    console.print()
    console.print(f"[bold]Linting:[/bold] {path}")
    console.print()

    # Read content
    content = path.read_text(encoding="utf-8")

    # Lint
    fixed_content, changes = lint_content(content)

    if not changes:
        console.print("[bold green]✓ No issues found[/bold green]")
        return

    # Show changes
    console.print(f"[bold]Found {len(changes)} issue(s):[/bold]")
    for change in changes:
        console.print(f"  🔧 {change}")
    console.print()

    if dry_run or not fix:
        if fix:
            pass  # Will apply below
        else:
            console.print("[dim]Run with --fix to apply changes[/dim]")
            return

    if fix:
        path.write_text(fixed_content, encoding="utf-8")
        console.print(f"[bold green]✓ Fixed {len(changes)} issue(s)[/bold green]")

        # Validate after fix
        console.print()
        console.print("[dim]Running validation...[/dim]")
        secrets = detect_secrets(fixed_content)
        structure = validate_structure(fixed_content)

        errors = [i for i in secrets + structure if i.get("type") == "error"]
        if errors:
            console.print("[bold yellow]⚠ Some issues remain:[/bold yellow]")
            for issue in errors:
                console.print(f"  {issue['message']}")
        else:
            console.print("[bold green]✓ File is now valid[/bold green]")


# ============================================================================
# Sprint 81: Context Command
# ============================================================================


def agents_context_command(
    project_id: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project ID (auto-detect from .sdlc/config.json if not provided)",
    ),
    format: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Output format: cli, json, pr_comment",
    ),
    api_url: Optional[str] = typer.Option(
        None,
        "--api-url",
        help="SDLC Orchestrator API URL (default: from config or http://localhost:8000)",
    ),
) -> None:
    """
    Fetch and display current SDLC context overlay.

    The context overlay includes:
    - Current SDLC stage and gate status
    - Active sprint information
    - Constraints and warnings
    - Strict mode status (post-G3)

    This command fetches the dynamic context from SDLC Orchestrator
    that would be posted as a GitHub Check Run annotation.

    Examples:

        sdlcctl agents context

        sdlcctl agents context --format json

        sdlcctl agents context --project abc123 --format pr_comment

        sdlcctl agents context --api-url https://api.sdlc.example.com
    """
    console.print()

    # Auto-detect project if not provided
    if not project_id:
        config_path = Path.cwd() / ".sdlc" / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                project_id = config.get("project_id")
                if project_id:
                    console.print(f"[dim]Auto-detected project: {project_id}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read .sdlc/config.json: {e}[/yellow]")

    if not project_id:
        console.print("[bold red]Error:[/bold red] No project ID found.")
        console.print()
        console.print("Either:")
        console.print("  1. Use --project <id> to specify project ID")
        console.print("  2. Create .sdlc/config.json with project_id")
        console.print()
        console.print("[bold]Example .sdlc/config.json:[/bold]")
        console.print('  {"project_id": "your-project-uuid"}')
        console.print()
        raise typer.Exit(code=1)

    # Determine API URL
    if not api_url:
        # Try to read from config
        config_path = Path.cwd() / ".sdlc" / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                api_url = config.get("api_url")
            except:
                pass

        if not api_url:
            api_url = os.getenv("SDLC_API_URL", "http://localhost:8000")

    # Fetch overlay
    console.print(f"[dim]Fetching context from {api_url}...[/dim]")
    console.print()

    try:
        import httpx

        response = httpx.get(
            f"{api_url}/api/v1/agents-md/context/{project_id}",
            timeout=30.0,
        )

        if response.status_code == 401:
            console.print("[bold red]Error:[/bold red] Authentication required.")
            console.print("Set SDLC_API_TOKEN environment variable or configure auth in .sdlc/config.json")
            raise typer.Exit(code=1)

        if response.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] Project not found: {project_id}")
            raise typer.Exit(code=1)

        if response.status_code != 200:
            console.print(f"[bold red]Error:[/bold red] API returned {response.status_code}")
            console.print(response.text)
            raise typer.Exit(code=1)

        overlay = response.json()

    except httpx.ConnectError:
        console.print(f"[bold red]Error:[/bold red] Could not connect to {api_url}")
        console.print("Make sure SDLC Orchestrator is running.")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Error fetching context:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Format output
    if format == "json":
        console.print_json(json.dumps(overlay, indent=2, default=str))

    elif format == "pr_comment":
        formatted = overlay.get("formatted", {})
        pr_comment = formatted.get("pr_comment", "")
        if pr_comment:
            console.print(pr_comment)
        else:
            console.print("[yellow]Warning: PR comment format not available[/yellow]")
            console.print_json(json.dumps(overlay, indent=2, default=str))

    else:
        # CLI format (default)
        stage_name = overlay.get("stage_name", "Unknown")
        gate_status = overlay.get("gate_status", "N/A")
        strict_mode = overlay.get("strict_mode", False)
        sprint = overlay.get("sprint")
        constraints = overlay.get("constraints", [])

        # Header panel
        header_lines = [
            f"[bold]Stage:[/bold] {stage_name}",
            f"[bold]Gate:[/bold] {gate_status}",
            f"[bold]Strict Mode:[/bold] {'🔒 YES' if strict_mode else 'No'}",
        ]

        if sprint:
            header_lines.extend([
                "",
                f"[bold]Sprint {sprint.get('number', 'N/A')}:[/bold] {sprint.get('goal', 'N/A')}",
                f"[dim]Days remaining: {sprint.get('days_remaining', 'N/A')}[/dim]",
            ])

        console.print(
            Panel(
                "\n".join(header_lines),
                title="[bold blue]SDLC Context Overlay[/bold blue]",
                border_style="blue",
            )
        )

        # Strict mode warning
        if strict_mode:
            console.print()
            console.print(
                Panel(
                    "[bold]⚠️ STRICT MODE ACTIVE[/bold]\n\n"
                    "Only bug fixes are allowed in this stage.\n"
                    "New features will be blocked by gate evaluation.",
                    title="[bold red]Warning[/bold red]",
                    border_style="red",
                )
            )

        # Constraints table
        if constraints:
            console.print()
            table = Table(title="Active Constraints", show_header=True)
            table.add_column("Type", style="cyan")
            table.add_column("Severity")
            table.add_column("Message")

            for c in constraints:
                severity = c.get("severity", "info")
                severity_icon = {
                    "info": "[blue]ℹ️ info[/blue]",
                    "warning": "[yellow]⚠️ warning[/yellow]",
                    "error": "[red]🔴 error[/red]",
                }.get(severity, severity)

                table.add_row(
                    c.get("type", "unknown").replace("_", " ").title(),
                    severity_icon,
                    c.get("message", ""),
                )

            console.print(table)

        console.print()
        console.print(f"[dim]Generated at: {overlay.get('generated_at', 'N/A')}[/dim]")
        console.print(f"[dim]Project ID: {project_id}[/dim]")

    console.print()


# ============================================================================
# Sprint 103: Validate Context Command (<60 Lines per File)
# ============================================================================


def agents_validate_context_command(
    path: Path = typer.Argument(
        ...,
        help="Path to AGENTS.md file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    max_lines: int = typer.Option(
        60,
        "--max-lines",
        "-m",
        help="Maximum lines per file context (default: 60)",
        min=10,
        max=200,
    ),
    format: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Output format: cli, json, github",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Exit with error code on any violation",
    ),
) -> None:
    """
    Validate per-file context limits in AGENTS.md.

    SDLC 6.0.0 requires that each file's context in AGENTS.md be concise
    (default: 60 lines max per file). This command parses AGENTS.md,
    extracts file-specific code blocks, and validates each against the limit.

    Context blocks are identified by headers like:
    - ### File: path/to/file.py
    - ## path/to/file.py
    - ### `path/to/file.ts`

    Followed by code blocks (```...```) containing the file's context.

    Examples:

        sdlcctl agents validate-context AGENTS.md

        sdlcctl agents validate-context AGENTS.md --max-lines 80

        sdlcctl agents validate-context AGENTS.md --format json

        sdlcctl agents validate-context AGENTS.md --format github --strict
    """
    console.print()
    console.print(
        Panel(
            "[bold]Per-File Context Validator[/bold]\n\n"
            f"Validates that each file's context in AGENTS.md is ≤{max_lines} lines.\n"
            "SDLC 6.0.0: Concise context for better AI comprehension.",
            title="[bold blue]sdlcctl agents validate-context[/bold blue]",
            border_style="blue",
        )
    )

    # Read content
    content = path.read_text(encoding="utf-8")

    # Parse file contexts
    file_contexts = _parse_file_contexts(content)

    # Find violations
    violations = [ctx for ctx in file_contexts if ctx["line_count"] > max_lines]

    # Output based on format
    if format == "json":
        result = {
            "valid": len(violations) == 0,
            "max_lines_allowed": max_lines,
            "total_files": len(file_contexts),
            "files_exceeding_limit": len(violations),
            "file_contexts": [
                {
                    "file_path": ctx["file_path"],
                    "line_count": ctx["line_count"],
                    "start_line": ctx["start_line"],
                    "end_line": ctx["end_line"],
                    "exceeds_limit": ctx["line_count"] > max_lines,
                }
                for ctx in file_contexts
            ],
            "violations": [
                {
                    "file_path": ctx["file_path"],
                    "line_count": ctx["line_count"],
                    "over_by": ctx["line_count"] - max_lines,
                }
                for ctx in violations
            ],
        }
        console.print_json(json.dumps(result, indent=2))

    elif format == "github":
        # GitHub Check Run / Actions format
        if violations:
            console.print()
            console.print("::group::Context Validation Violations")
            for ctx in violations:
                # GitHub annotation format
                console.print(
                    f"::error file=AGENTS.md,line={ctx['start_line']}::"
                    f"File '{ctx['file_path']}' context exceeds {max_lines}-line limit "
                    f"({ctx['line_count']} lines, {ctx['line_count'] - max_lines} over)"
                )
            console.print("::endgroup::")
            console.print()
            console.print(
                f"::error::Context validation failed: {len(violations)} file(s) exceed "
                f"{max_lines}-line limit"
            )
        else:
            console.print(
                f"::notice::Context validation passed: {len(file_contexts)} file(s) "
                f"within {max_lines}-line limit"
            )

    else:
        # CLI format (default)
        console.print()

        if file_contexts:
            table = Table(title="File Contexts in AGENTS.md", show_header=True)
            table.add_column("File", style="cyan", width=40)
            table.add_column("Lines", justify="right", width=8)
            table.add_column("Limit", justify="right", width=8)
            table.add_column("Status", justify="center", width=12)

            for ctx in file_contexts:
                line_count = ctx["line_count"]
                exceeds = line_count > max_lines

                if exceeds:
                    status = f"[bold red]❌ +{line_count - max_lines}[/bold red]"
                elif line_count > max_lines * 0.8:
                    status = "[yellow]⚠️ near limit[/yellow]"
                else:
                    status = "[green]✓[/green]"

                table.add_row(
                    ctx["file_path"][:38] + "..." if len(ctx["file_path"]) > 40 else ctx["file_path"],
                    str(line_count),
                    str(max_lines),
                    status,
                )

            console.print(table)
        else:
            console.print("[dim]No file-specific contexts found in AGENTS.md.[/dim]")
            console.print("[dim]File contexts are identified by headers like '### File: path/to/file.py'[/dim]")

        # Summary
        console.print()
        console.print("[bold]Summary:[/bold]")
        console.print(f"  📁 Total file contexts: {len(file_contexts)}")
        console.print(f"  📏 Max lines allowed: {max_lines}")
        console.print(f"  ❌ Violations: {len(violations)}")

        if violations:
            console.print()
            console.print("[bold red]Violations:[/bold red]")
            for ctx in violations:
                console.print(
                    f"  • {ctx['file_path']}: {ctx['line_count']} lines "
                    f"(+{ctx['line_count'] - max_lines} over limit)"
                )

    # Exit code
    console.print()
    if violations:
        console.print("[bold red]✗ Context validation FAILED[/bold red]")
        console.print(f"  {len(violations)} file(s) exceed the {max_lines}-line limit")
        console.print()
        console.print("[bold]Recommendations:[/bold]")
        console.print("  1. Focus each file context on the most critical information")
        console.print("  2. Extract reusable patterns to a 'Conventions' section")
        console.print("  3. Move detailed docs to separate files and reference them")
        console.print("  4. Use PR comments for dynamic context (Sprint 81)")
        if strict:
            raise typer.Exit(code=1)
    else:
        console.print("[bold green]✓ Context validation PASSED[/bold green]")
        console.print(f"  All {len(file_contexts)} file contexts are within the {max_lines}-line limit")

    console.print()


def _parse_file_contexts(content: str) -> List[dict]:
    """
    Parse AGENTS.md to extract file-specific code blocks.

    Identifies file contexts by looking for headers that reference file paths,
    followed by code blocks containing the file's context.

    Supported header formats:
    - ### File: path/to/file.py
    - ## path/to/file.py
    - ### `path/to/file.ts`
    - #### src/components/Button.tsx

    Returns:
        List of dicts with file_path, line_count, start_line, end_line
    """
    file_contexts = []
    lines = content.split('\n')

    # Patterns to match file headers
    file_header_patterns = [
        # ### File: path/to/file.py
        re.compile(r'^#{2,4}\s+[Ff]ile:\s*`?([^\s`]+)`?\s*$'),
        # ### path/to/file.py (with extension)
        re.compile(r'^#{2,4}\s+`?([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)`?\s*$'),
        # ### `path/to/file.py`
        re.compile(r'^#{2,4}\s+`([^`]+)`\s*$'),
    ]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line matches any file header pattern
        file_path = None
        for pattern in file_header_patterns:
            match = pattern.match(line)
            if match:
                file_path = match.group(1)
                break

        if file_path:
            header_line = i + 1  # 1-indexed

            # Look for code block(s) following this header
            j = i + 1
            code_block_lines = 0
            code_block_start = None
            code_block_end = None
            in_code_block = False

            while j < len(lines):
                current = lines[j]

                # Check for code block start/end
                if current.startswith('```'):
                    if not in_code_block:
                        # Start of code block
                        in_code_block = True
                        if code_block_start is None:
                            code_block_start = j + 1  # 1-indexed
                    else:
                        # End of code block
                        in_code_block = False
                        code_block_end = j + 1  # 1-indexed
                elif in_code_block:
                    code_block_lines += 1

                # Stop if we hit another file header or major section
                if not in_code_block and j > i + 1:
                    if re.match(r'^#{1,4}\s+', current):
                        # Check if it's a new file header
                        is_new_file = any(p.match(current) for p in file_header_patterns)
                        if is_new_file:
                            break
                        # Check if it's a major section (not a sub-header under this file)
                        if re.match(r'^#{1,2}\s+', current):
                            break

                j += 1

            if code_block_lines > 0:
                file_contexts.append({
                    "file_path": file_path,
                    "line_count": code_block_lines,
                    "start_line": code_block_start or header_line,
                    "end_line": code_block_end or j,
                })

            i = j
        else:
            i += 1

    return file_contexts
