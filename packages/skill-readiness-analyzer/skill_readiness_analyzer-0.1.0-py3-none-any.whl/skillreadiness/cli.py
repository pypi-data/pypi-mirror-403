"""Command-line interface for skill readiness analyzer."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from skillreadiness import __version__
from skillreadiness.core.models import ScanResult, Severity
from skillreadiness.core.orchestrator import get_orchestrator
from skillreadiness.core.taxonomy import format_taxonomy_overview
from skillreadiness.providers import get_default_providers
from skillreadiness.reports import render_json, render_markdown, render_sarif

console = Console()


def get_readiness_color(score: int) -> str:
    """Get color for readiness score."""
    if score >= 90:
        return "green"
    elif score >= 70:
        return "yellow"
    elif score >= 50:
        return "orange1"
    else:
        return "red"


def get_severity_color(severity: Severity) -> str:
    """Get color for severity level."""
    return {
        Severity.CRITICAL: "red",
        Severity.HIGH: "orange1",
        Severity.MEDIUM: "yellow",
        Severity.LOW: "blue",
        Severity.INFO: "dim",
    }.get(severity, "white")


def print_scan_result(result: ScanResult, verbose: bool = False) -> None:
    """Print scan result to console."""
    console.print()
    console.print("=" * 60)
    console.print(f"[bold]Skill: {result.skill_name}[/bold]")
    console.print("=" * 60)

    score_color = get_readiness_color(result.readiness_score)
    console.print(
        f"Readiness Score: [{score_color}]{result.readiness_score}/100[/{score_color}] "
        f"([{score_color}]{result.readiness_label}[/{score_color}])"
    )
    console.print()

    if not result.findings:
        console.print("[green]No issues found![/green]")
        return

    for finding in sorted(result.findings, key=lambda f: f.severity.value):
        severity_color = get_severity_color(finding.severity)
        severity_label = finding.severity.value.upper()

        console.print(
            f"[{severity_color}]{severity_label}[/{severity_color}]: "
            f"[bold]{finding.rule_id or 'N/A'}[/bold] - {finding.title}"
        )
        console.print(f"    → {finding.description}")

        if finding.location:
            console.print(f"    → Location: {finding.location}")

        if finding.remediation:
            console.print(f"    → Remediation: {finding.remediation}")

        if verbose and finding.evidence:
            console.print(f"    → Evidence: {finding.evidence}")

        console.print()


def output_result(
    result: ScanResult,
    format: str,
    output_file: str | None,
    verbose: bool,
) -> None:
    """Output result in specified format."""
    if format == "json":
        content = render_json(result, indent=2)
    elif format == "markdown":
        content = render_markdown(result, verbose=verbose)
    elif format == "sarif":
        content = render_sarif(result)
    else:
        print_scan_result(result, verbose=verbose)
        return

    if output_file:
        Path(output_file).write_text(content)
        console.print(f"[green]Report written to {output_file}[/green]")
    else:
        print(content)


@click.group()
@click.version_option(version=__version__, prog_name="skill-readiness")
def cli() -> None:
    """Skill Readiness Analyzer - Production readiness scanner for AI Agent Skills."""
    pass


@cli.command("scan")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["summary", "json", "markdown", "sarif"]),
    default="summary",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"]),
    default=None,
    help="Exit with error if findings at or above severity",
)
def scan_command(
    path: str,
    format: str,
    output: str | None,
    verbose: bool,
    fail_on: str | None,
) -> None:
    """Scan a single skill directory for readiness issues."""
    orchestrator = get_orchestrator()
    result = orchestrator.scan_skill_sync(path)

    output_result(result, format, output, verbose)

    if fail_on:
        severity_order = ["critical", "high", "medium", "low"]
        fail_threshold = severity_order.index(fail_on)

        for finding in result.findings:
            finding_level = severity_order.index(finding.severity.value)
            if finding_level <= fail_threshold:
                sys.exit(1)


@cli.command("scan-skills")
@click.argument("path", type=click.Path(exists=True))
@click.option("--glob", "-g", default="*/SKILL.md", help="Glob pattern to find skills")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["summary", "json", "markdown"]),
    default="summary",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def scan_skills_command(
    path: str,
    glob: str,
    format: str,
    output: str | None,
    verbose: bool,
) -> None:
    """Scan multiple skills in a directory."""
    orchestrator = get_orchestrator()
    result = orchestrator.scan_skills_sync(path, glob)

    if format == "summary":
        console.print()
        console.print(f"[bold]Scanned {result.total_skills_scanned} skills[/bold]")
        console.print(f"Total findings: {result.total_findings}")
        console.print(f"Average readiness: {result.average_readiness_score:.1f}/100")
        console.print(f"Production ready: {result.skills_production_ready}/{result.total_skills_scanned}")
        console.print()

        for scan_result in result.scan_results:
            print_scan_result(scan_result, verbose=verbose)
    elif format == "json":
        content = result.model_dump_json(indent=2)
        if output:
            Path(output).write_text(content)
            console.print(f"[green]Report written to {output}[/green]")
        else:
            print(content)
    elif format == "markdown":
        lines = [
            "# Skill Readiness Scan Results",
            "",
            f"**Skills Scanned:** {result.total_skills_scanned}",
            f"**Total Findings:** {result.total_findings}",
            f"**Average Score:** {result.average_readiness_score:.1f}/100",
            f"**Production Ready:** {result.skills_production_ready}/{result.total_skills_scanned}",
            "",
        ]
        for scan_result in result.scan_results:
            lines.append(render_markdown(scan_result, verbose=verbose))
            lines.append("")

        content = "\n".join(lines)
        if output:
            Path(output).write_text(content)
            console.print(f"[green]Report written to {output}[/green]")
        else:
            print(content)


@cli.command("list-categories")
def list_categories_command() -> None:
    """List all readiness check categories."""
    console.print(format_taxonomy_overview())


@cli.command("list-providers")
def list_providers_command() -> None:
    """List available inspection providers."""
    providers = get_default_providers()

    table = Table(title="Available Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Status", style="green")

    for provider in providers:
        status = "Available" if provider.is_available() else f"Unavailable: {provider.get_unavailable_reason()}"
        status_style = "green" if provider.is_available() else "red"
        table.add_row(
            provider.name,
            provider.description,
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)


@cli.command("init")
@click.option("--format", "-f", type=click.Choice(["toml", "yaml"]), default="toml")
def init_command(format: str) -> None:
    """Generate a sample configuration file."""
    if format == "toml":
        content = '''# Skill Readiness Analyzer Configuration

[scan]
timeout_seconds = 30.0

[output]
format = "summary"
verbose = false

[heuristic]
max_lines = 500
max_tokens = 2000
min_description_length = 50

[fail]
# Set to fail CI on findings at or above severity
# severity = "high"
'''
        filename = ".skill-readiness.toml"
    else:
        content = '''# Skill Readiness Analyzer Configuration

scan:
  timeout_seconds: 30.0

output:
  format: summary
  verbose: false

heuristic:
  max_lines: 500
  max_tokens: 2000
  min_description_length: 50

fail:
  # Set to fail CI on findings at or above severity
  # severity: high
'''
        filename = ".skill-readiness.yaml"

    Path(filename).write_text(content)
    console.print(f"[green]Configuration written to {filename}[/green]")


if __name__ == "__main__":
    cli()
