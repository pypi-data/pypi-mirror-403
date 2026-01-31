"""
=========================================================================
SDLC 5.3.0 Structure Validator CLI.
SDLC Orchestrator - Sprint 119

Version: 3.2.0
Date: January 29, 2026
Status: ACTIVE - Sprint 119 Specification CLI
Authority: Backend Team + CTO Approved
Reference: SPEC-0002-Specification-Standard

Purpose:
- Main entry point for the sdlcctl command-line tool
- Structure validation, fixing, and initialization
- Code generation from AppBlueprint (Sprint 46)
- Magic Mode - Natural language to code (Sprint 52)
- Planning Mode - Sub-agent orchestration (Sprint 98)
- Conformance Check - PR pattern validation (Sprint 99)
- Specification Validation - Framework 6.0.0 specs (Sprint 119)

Usage:
    sdlcctl validate ./my-project
    sdlcctl generate blueprint.json -o ./output
    sdlcctl magic "Nhà hàng Phở 24" -o ./pho24
    sdlcctl plan new "Add OAuth2 authentication"
    sdlcctl plan check --diff changes.diff
    sdlcctl spec validate docs/02-design/14-Technical-Specs/
    sdlcctl spec list --tier PROFESSIONAL
=========================================================================
"""

import typer
from rich.console import Console

from . import __version__, __framework__
from .commands.validate import validate_command
from .commands.fix import fix_command
from .commands.init import init_command
from .commands.report import report_command
from .commands.migrate import migrate_command
from .commands.generate import generate_command
from .commands.magic import magic_command
from .commands.plan import plan_command, check_command
from .commands.agents import (
    agents_init_command,
    agents_validate_command,
    agents_lint_command,
    agents_context_command,
    agents_validate_context_command,
)
from .commands.spec import app as spec_app
from .commands.compliance import (
    compliance_score,
    compliance_duplicates,
    compliance_report,
    compliance_categories,
)

console = Console()

# Create main Typer app
app = typer.Typer(
    name="sdlcctl",
    help="SDLC 5.0.0 Structure Validator CLI",
    add_completion=True,
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version information."""
    if value:
        console.print(f"[bold blue]sdlcctl[/bold blue] v{__version__}")
        console.print(f"[dim]Framework: {__framework__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    SDLC 5.0.0 Structure Validator CLI.

    Validate, fix, and initialize SDLC 5.0.0 compliant project structures.

    Supports 4-Tier Classification:
    - LITE: 1-2 people, 4 stages
    - STANDARD: 3-10 people, 6 stages
    - PROFESSIONAL: 10-50 people, 10 stages (P0 required)
    - ENTERPRISE: 50+ people, 11 stages (full compliance)
    """
    pass


# Register commands
app.command(name="validate", help="Validate SDLC 5.0.0 folder structure")(
    validate_command
)
app.command(name="fix", help="Automatically fix SDLC structure issues")(
    fix_command
)
app.command(name="init", help="Initialize SDLC 5.0.0 project structure")(
    init_command
)
app.command(name="report", help="Generate SDLC compliance report")(
    report_command
)
app.command(name="migrate", help="Migrate from SDLC 4.9.x to 5.0.0")(
    migrate_command
)
app.command(name="generate", help="Generate backend scaffold from AppBlueprint")(
    generate_command
)
app.command(name="magic", help="Generate app from natural language (Vietnamese/English)")(
    magic_command
)
# Create plan sub-app for planning mode commands (Sprint 98-99)
plan_app = typer.Typer(
    name="plan",
    help="Planning mode with sub-agent orchestration (ADR-034)",
    no_args_is_help=True,
)

plan_app.command(name="new", help="Create new planning session with pattern extraction")(
    plan_command
)
plan_app.command(name="check", help="Check PR/diff conformance against established patterns")(
    check_command
)

# Register plan sub-app
app.add_typer(plan_app, name="plan")

# Keep standalone plan command for backward compatibility
app.command(name="plan-legacy", help="[Deprecated] Use 'plan new' instead", hidden=True)(
    plan_command
)

# Create agents sub-app for AGENTS.md commands (Sprint 80/81)
agents_app = typer.Typer(
    name="agents",
    help="AGENTS.md management commands (ADR-029)",
    no_args_is_help=True,
)

agents_app.command(name="init", help="Generate AGENTS.md from project analysis")(
    agents_init_command
)
agents_app.command(name="validate", help="Validate AGENTS.md structure and content")(
    agents_validate_command
)
agents_app.command(name="lint", help="Lint and auto-fix AGENTS.md")(
    agents_lint_command
)
agents_app.command(name="context", help="Fetch current SDLC context overlay (Sprint 81)")(
    agents_context_command
)
agents_app.command(name="validate-context", help="Validate per-file context limits (<60 lines) (Sprint 103)")(
    agents_validate_context_command
)

# Register agents sub-app
app.add_typer(agents_app, name="agents")

# Register spec sub-app (Sprint 119 - Specification validation)
app.add_typer(spec_app, name="spec")

# Create compliance sub-app for SDLC 6.0.0 compliance validation (Sprint 123)
compliance_app = typer.Typer(
    name="compliance",
    help="SDLC 6.0.0 compliance validation (SPEC-0013)",
    no_args_is_help=True,
)

compliance_app.command(name="score", help="Calculate compliance score (10 categories × 10 pts)")(
    compliance_score
)
compliance_app.command(name="duplicates", help="Detect duplicate stage folders")(
    compliance_duplicates
)
compliance_app.command(name="report", help="Generate comprehensive compliance report")(
    compliance_report
)
compliance_app.command(name="categories", help="Show compliance category definitions")(
    compliance_categories
)

# Register compliance sub-app
app.add_typer(compliance_app, name="compliance")


@app.command(name="tiers")
def show_tiers() -> None:
    """Show tier classification details."""
    from rich.table import Table

    from .validation.tier import TIER_REQUIREMENTS, Tier

    table = Table(title="SDLC 5.0.0 Tier Classification", show_header=True)
    table.add_column("Tier", style="cyan", width=15)
    table.add_column("Team Size", justify="right", width=12)
    table.add_column("Stages", justify="right", width=10)
    table.add_column("P0 Required", justify="center", width=12)
    table.add_column("Compliance", width=20)

    tier_sizes = {
        Tier.LITE: "1-2",
        Tier.STANDARD: "3-10",
        Tier.PROFESSIONAL: "10-50",
        Tier.ENTERPRISE: "50+",
    }

    for tier, req in TIER_REQUIREMENTS.items():
        compliance = ", ".join(req.compliance_required) if req.compliance_required else "-"
        table.add_row(
            tier.value.upper(),
            tier_sizes[tier],
            str(req.min_stages),
            "✅" if req.p0_required else "❌",
            compliance,
        )

    console.print()
    console.print(table)
    console.print()


@app.command(name="stages")
def show_stages() -> None:
    """Show SDLC 5.0.0 stage definitions (Contract-First Order)."""
    from rich.table import Table

    from .validation.tier import STAGE_NAMES

    table = Table(title="SDLC 5.0.0 Stages (Contract-First Order)", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Stage Name", width=20)
    table.add_column("Purpose", width=50)
    table.add_column("Type", width=12)

    # SDLC 5.1.3 Stage Definitions (10 Stages: 00-09 + Archive folder)
    # Reference: SDLC-Enterprise-Framework/README.md (v5.1.1)
    questions = {
        "00": ("FOUNDATION - Strategic Discovery & Validation (WHY?)", "LINEAR"),
        "01": ("PLANNING - Requirements & User Stories (WHAT?)", "LINEAR"),
        "02": ("DESIGN - Architecture & Technical Design (HOW?)", "LINEAR"),
        "03": ("INTEGRATE - API Contracts & Third-party Setup", "LINEAR"),
        "04": ("BUILD - Development & Implementation", "LINEAR"),
        "05": ("TEST - Quality Assurance & Validation", "LINEAR"),
        "06": ("DEPLOY - Release & Deployment", "LINEAR"),
        "07": ("OPERATE - Production Operations & Monitoring", "LINEAR"),
        "08": ("COLLABORATE - Team Coordination & Knowledge", "CONTINUOUS"),
        "09": ("GOVERN - Compliance & Strategic Oversight", "CONTINUOUS"),
        "10": ("ARCHIVE - Project Archive (Legacy Docs)", "OPTIONAL"),
    }

    for stage_id, stage_name in sorted(STAGE_NAMES.items()):
        purpose, stage_type = questions.get(stage_id, ("", ""))
        table.add_row(stage_id, stage_name, purpose, stage_type)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Contract-First: API Design (Stage 03) must happen BEFORE coding (Stage 04)[/dim]")
    console.print()


@app.command(name="p0")
def show_p0() -> None:
    """Show P0 artifact requirements."""
    from rich.table import Table

    from .validation.p0 import P0_ARTIFACTS
    from .validation.tier import Tier

    table = Table(title="SDLC 5.0.0 P0 Artifacts", show_header=True)
    table.add_column("Artifact", style="cyan", width=25)
    table.add_column("Stage", width=8)
    table.add_column("Path", width=45)
    table.add_column("LITE", justify="center", width=6)
    table.add_column("STD", justify="center", width=6)
    table.add_column("PRO", justify="center", width=6)
    table.add_column("ENT", justify="center", width=6)

    for artifact in P0_ARTIFACTS:
        table.add_row(
            artifact.name,
            artifact.stage_id,
            artifact.relative_path[:42] + "..." if len(artifact.relative_path) > 45 else artifact.relative_path,
            "✅" if Tier.LITE in artifact.required_tiers else "❌",
            "✅" if Tier.STANDARD in artifact.required_tiers else "❌",
            "✅" if Tier.PROFESSIONAL in artifact.required_tiers else "❌",
            "✅" if Tier.ENTERPRISE in artifact.required_tiers else "❌",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Total P0 Artifacts: {len(P0_ARTIFACTS)}[/dim]")
    console.print()


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()
