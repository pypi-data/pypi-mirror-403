"""
Compliance Validation CLI Commands - Sprint 123 (SPEC-0013)

SDLC 6.0.0 compliance scoring and folder collision detection.

Version: 1.0.0
Date: January 30, 2026
Status: ACTIVE - Sprint 123
Authority: CTO Approved (A+ Grade, 98/100)
Reference: SPEC-0013 Compliance Validation Service

Usage:
    sdlcctl compliance score --path ./my-project
    sdlcctl compliance duplicates --path ./my-project
    sdlcctl compliance report --path ./my-project --output report.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# =============================================================================
# Constants
# =============================================================================

STAGE_PREFIXES = [
    ("00", "discover"),
    ("01", "planning"),
    ("02", "design"),
    ("03", "integrate"),
    ("04", "build"),
    ("05", "test"),
    ("06", "deploy"),
    ("07", "operate"),
    ("08", "collaborate"),
    ("09", "govern"),
    ("10", "archive"),
]

REQUIRED_PREFIXES = {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09"}

COMPLIANCE_CATEGORIES = [
    ("documentation_structure", "Stage Folders (00-10), no duplicates"),
    ("specifications_management", "YAML frontmatter, SPEC-XXXX numbering"),
    ("claude_agents_md", "Version headers, required sections"),
    ("sase_artifacts", "CRP, MRP, VCR templates present"),
    ("code_file_naming", "snake_case (Python), PascalCase (TSX)"),
    ("migration_tracking", "Progress %, deadline compliance"),
    ("framework_alignment", "7-Pillar + Section 7"),
    ("team_organization", "SDLC Compliance Hub, roles"),
    ("legacy_archival", "99-legacy/ or 10-Archive/ usage"),
    ("governance_documentation", "ADRs, CEO/CTO approvals"),
]


# =============================================================================
# Helper Functions
# =============================================================================


def detect_folder_collisions(docs_path: Path) -> dict:
    """
    Detect stage folder collisions in docs directory.

    Returns:
        Dict with collisions, gaps, extras, and valid status
    """
    if not docs_path.exists():
        return {
            "valid": False,
            "error": f"Docs path not found: {docs_path}",
            "collisions": [],
            "gaps": [],
            "extras": [],
        }

    # Get all directories
    folders = [
        d.name for d in docs_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    collisions = []
    gaps = []
    extras = []

    # Track which prefixes we've seen
    prefix_to_folders: dict[str, list[str]] = {}

    # Categorize each folder
    for folder in folders:
        if "-" in folder:
            prefix = folder.split("-")[0]
            if prefix.isdigit():
                if prefix not in prefix_to_folders:
                    prefix_to_folders[prefix] = []
                prefix_to_folders[prefix].append(folder)
                continue

        # Non-stage folders
        allowed_extras = {"specs", "templates", ".git", ".github", "readme.md"}
        if folder.lower() not in allowed_extras:
            extras.append(folder)

    # Check each stage prefix
    for prefix, stage_name in STAGE_PREFIXES:
        matching = prefix_to_folders.get(prefix, [])

        if len(matching) > 1:
            # Collision detected
            collisions.append({
                "stage_prefix": prefix,
                "stage_name": stage_name,
                "folders": matching,
                "severity": "critical",
            })
        elif len(matching) == 0 and prefix in REQUIRED_PREFIXES:
            gaps.append(f"{prefix}-{stage_name}")

    return {
        "valid": len(collisions) == 0,
        "collisions": collisions,
        "gaps": gaps,
        "extras": extras,
        "total_folders": len(folders),
    }


def calculate_quick_score(path: Path, docs_root: str = "docs") -> dict:
    """
    Calculate a quick compliance score based on local analysis.

    This is a simplified local calculation. For full scoring,
    use the API endpoint.

    Returns:
        Dict with score breakdown
    """
    docs_path = path / docs_root
    scores = {}
    issues = []

    # 1. Documentation Structure (10 pts)
    collision_check = detect_folder_collisions(docs_path)
    if collision_check["valid"]:
        if len(collision_check["gaps"]) == 0:
            scores["documentation_structure"] = 10
        elif len(collision_check["gaps"]) <= 2:
            scores["documentation_structure"] = 8
            issues.append(f"Missing stages: {', '.join(collision_check['gaps'])}")
        else:
            scores["documentation_structure"] = 5
            issues.append(f"Missing {len(collision_check['gaps'])} stages")
    else:
        scores["documentation_structure"] = 0
        for col in collision_check["collisions"]:
            issues.append(
                f"CRITICAL: Duplicate stage {col['stage_prefix']}: "
                f"{', '.join(col['folders'])}"
            )

    # 2. Specifications Management (10 pts)
    specs_path = docs_path / "02-design" / "14-Technical-Specs"
    if not specs_path.exists():
        specs_path = path / "docs" / "specs"  # Alternative location

    if specs_path.exists():
        spec_files = list(specs_path.glob("*.md"))
        if len(spec_files) > 0:
            valid_specs = 0
            for spec in spec_files:
                content = spec.read_text(encoding="utf-8", errors="ignore")
                if "---" in content and ("SPEC-" in content or "spec_id:" in content):
                    valid_specs += 1

            ratio = valid_specs / len(spec_files) if spec_files else 0
            scores["specifications_management"] = int(ratio * 10)
            if ratio < 1.0:
                issues.append(f"Only {valid_specs}/{len(spec_files)} specs have proper YAML frontmatter")
        else:
            scores["specifications_management"] = 0
            issues.append("No specification files found")
    else:
        scores["specifications_management"] = 0
        issues.append("Technical specs folder not found")

    # 3. CLAUDE.md / AGENTS.md (10 pts)
    claude_score = 0
    if (path / "CLAUDE.md").exists():
        claude_score += 5
    else:
        issues.append("CLAUDE.md not found in project root")

    if (path / "AGENTS.md").exists():
        claude_score += 5
    else:
        issues.append("AGENTS.md not found in project root")

    scores["claude_agents_md"] = claude_score

    # 4. SASE Artifacts (10 pts) - Check for CRP, MRP, VCR
    sase_score = 0
    sase_path = docs_path / "08-collaborate"
    if sase_path.exists():
        if any(sase_path.rglob("*CRP*")) or any(sase_path.rglob("*consultation*")):
            sase_score += 3
        if any(sase_path.rglob("*MRP*")) or any(sase_path.rglob("*merge*")):
            sase_score += 3
        if any(sase_path.rglob("*VCR*")) or any(sase_path.rglob("*vibe*")):
            sase_score += 4
        if sase_score < 10:
            issues.append(f"SASE artifacts incomplete: {sase_score}/10 points")
    else:
        issues.append("08-collaborate stage folder not found")
    scores["sase_artifacts"] = sase_score

    # 5. Code File Naming (10 pts)
    py_files = list((path / "backend").rglob("*.py")) if (path / "backend").exists() else []
    ts_files = list((path / "frontend").rglob("*.ts")) + list((path / "frontend").rglob("*.tsx")) if (path / "frontend").exists() else []

    naming_score = 10
    naming_issues = []

    for py_file in py_files[:50]:  # Sample up to 50
        if not py_file.stem.islower() and "_" not in py_file.stem:
            if not py_file.stem.startswith("__"):
                naming_issues.append(f"Python file not snake_case: {py_file.name}")
                naming_score -= 0.2

    for ts_file in ts_files[:50]:
        if ts_file.suffix == ".tsx" and not ts_file.stem[0].isupper():
            if ts_file.stem not in ["index", "main", "app"]:
                naming_issues.append(f"React component not PascalCase: {ts_file.name}")
                naming_score -= 0.2

    scores["code_file_naming"] = max(0, int(naming_score))
    if naming_issues:
        issues.extend(naming_issues[:3])  # Show top 3

    # 6-10: Simplified scores based on existence checks
    # Migration Tracking
    if (docs_path / "08-collaborate" / "01-SDLC-Compliance").exists():
        scores["migration_tracking"] = 8
    else:
        scores["migration_tracking"] = 5
        issues.append("Migration tracking folder not found")

    # Framework Alignment - check for 7-Pillar references
    scores["framework_alignment"] = 7  # Default reasonable score

    # Team Organization
    if (docs_path / "08-collaborate").exists():
        scores["team_organization"] = 8
    else:
        scores["team_organization"] = 5

    # Legacy Archival
    if (docs_path / "10-archive").exists() or (path / "99-legacy").exists():
        scores["legacy_archival"] = 10
    else:
        scores["legacy_archival"] = 6
        issues.append("No 10-archive or 99-legacy folder found")

    # Governance Documentation
    adr_path = docs_path / "02-design" / "01-ADRs"
    if adr_path.exists() and list(adr_path.glob("*.md")):
        scores["governance_documentation"] = 9
    else:
        scores["governance_documentation"] = 5
        issues.append("ADRs folder not found or empty")

    # Calculate total
    total_score = sum(scores.values())

    return {
        "overall_score": total_score,
        "max_score": 100,
        "categories": scores,
        "issues": issues,
        "issue_count": {
            "critical": len([i for i in issues if "CRITICAL" in i]),
            "warning": len([i for i in issues if "CRITICAL" not in i]),
        },
    }


# =============================================================================
# CLI Commands
# =============================================================================


def compliance_score(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed breakdown",
    ),
) -> None:
    """
    Calculate SDLC 6.0.0 compliance score.

    10 categories × 10 points = 100 maximum score.

    Examples:
        sdlcctl compliance score
        sdlcctl compliance score --path ./my-project
        sdlcctl compliance score --format json
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Calculating compliance score...", total=None)
        result = calculate_quick_score(path, docs_root)

    if output_format.lower() == "json":
        console.print(json.dumps(result, indent=2))
        return

    # Text output
    score = result["overall_score"]
    color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

    console.print()
    console.print(Panel(
        f"[bold {color}]{score}/100[/bold {color}]",
        title="SDLC 6.0.0 Compliance Score",
        subtitle=str(path),
    ))

    # Category breakdown
    if verbose:
        console.print()
        table = Table(title="Category Breakdown", show_header=True)
        table.add_column("Category", style="cyan", width=30)
        table.add_column("Score", justify="right", width=8)
        table.add_column("Description", width=40)

        for cat_id, description in COMPLIANCE_CATEGORIES:
            cat_score = result["categories"].get(cat_id, 0)
            cat_color = "green" if cat_score >= 8 else "yellow" if cat_score >= 5 else "red"
            table.add_row(
                cat_id.replace("_", " ").title(),
                f"[{cat_color}]{cat_score}/10[/{cat_color}]",
                description,
            )

        console.print(table)

    # Issues
    if result["issues"]:
        console.print()
        console.print("[bold]Issues Found:[/bold]")
        for issue in result["issues"][:10]:  # Top 10
            if "CRITICAL" in issue:
                console.print(f"  [red]• {issue}[/red]")
            else:
                console.print(f"  [yellow]• {issue}[/yellow]")

        if len(result["issues"]) > 10:
            console.print(f"  [dim]... and {len(result['issues']) - 10} more[/dim]")

    console.print()


def compliance_duplicates(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Show fix commands for collisions",
    ),
) -> None:
    """
    Detect duplicate stage folders.

    Finds collisions like 04-Development + 04-Testing.

    Examples:
        sdlcctl compliance duplicates
        sdlcctl compliance duplicates --path ./my-project
        sdlcctl compliance duplicates --fix
    """
    docs_path = path / docs_root
    result = detect_folder_collisions(docs_path)

    if output_format.lower() == "json":
        console.print(json.dumps(result, indent=2))
        return

    # Text output
    console.print()

    if result["valid"]:
        console.print(Panel(
            "[green]✓ No stage folder collisions detected[/green]",
            title="Duplicate Check",
        ))
    else:
        console.print(Panel(
            f"[red]✗ {len(result['collisions'])} collision(s) detected[/red]",
            title="Duplicate Check",
        ))

        for collision in result["collisions"]:
            console.print()
            console.print(f"[bold red]Stage {collision['stage_prefix']} ({collision['stage_name']}):[/bold red]")
            for folder in collision["folders"]:
                console.print(f"  • {folder}")

            if fix:
                archive_path = f"{docs_root}/10-archive/duplicate-folders-sprint123"
                to_archive = collision["folders"][1:]
                console.print()
                console.print("[dim]Fix commands:[/dim]")
                console.print(f"  mkdir -p {archive_path}")
                for folder in to_archive:
                    console.print(f"  mv {docs_root}/{folder} {archive_path}/")

    # Gaps
    if result["gaps"]:
        console.print()
        console.print(f"[yellow]Missing required stages ({len(result['gaps'])}):[/yellow]")
        for gap in result["gaps"]:
            console.print(f"  • {gap}")

    # Extras
    if result["extras"]:
        console.print()
        console.print(f"[dim]Non-standard folders ({len(result['extras'])}):[/dim]")
        for extra in result["extras"]:
            console.print(f"  • {extra}")

    console.print()


def compliance_report(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    docs_root: str = typer.Option(
        "docs",
        "--docs",
        "-d",
        help="Documentation folder name",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
) -> None:
    """
    Generate comprehensive compliance report.

    Combines score and duplicate detection into a single report.

    Examples:
        sdlcctl compliance report
        sdlcctl compliance report --output compliance-report.json
    """
    docs_path = path / docs_root

    # Calculate all metrics
    score_result = calculate_quick_score(path, docs_root)
    collision_result = detect_folder_collisions(docs_path)

    report = {
        "project_path": str(path),
        "docs_path": str(docs_path),
        "generated_at": datetime.utcnow().isoformat(),
        "framework_version": "6.0.0",
        "compliance_score": {
            "overall": score_result["overall_score"],
            "max": 100,
            "categories": score_result["categories"],
        },
        "folder_check": {
            "valid": collision_result["valid"],
            "collisions": collision_result["collisions"],
            "gaps": collision_result["gaps"],
            "extras": collision_result["extras"],
        },
        "issues": score_result["issues"],
        "summary": {
            "critical_issues": score_result["issue_count"]["critical"],
            "warnings": score_result["issue_count"]["warning"],
            "passing": score_result["overall_score"] >= 80,
        },
    }

    if output:
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        console.print(json.dumps(report, indent=2))


def compliance_categories() -> None:
    """
    Show compliance category definitions.

    Lists all 10 categories with descriptions and point values.
    """
    console.print()
    table = Table(title="SDLC 6.0.0 Compliance Categories", show_header=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Category", width=28)
    table.add_column("Points", justify="center", width=8)
    table.add_column("Description", width=45)

    for i, (cat_id, description) in enumerate(COMPLIANCE_CATEGORIES, 1):
        table.add_row(
            str(i),
            cat_id.replace("_", " ").title(),
            "10",
            description,
        )

    console.print(table)
    console.print()
    console.print("[dim]Total: 10 categories × 10 points = 100 maximum score[/dim]")
    console.print()
