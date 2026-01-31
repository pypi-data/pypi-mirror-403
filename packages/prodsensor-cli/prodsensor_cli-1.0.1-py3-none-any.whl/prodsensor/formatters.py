"""
Output formatters for ProdSensor CLI
"""

import json
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from prodsensor.client import AnalysisResult, Verdict


console = Console()


def format_verdict_color(verdict: Optional[Verdict]) -> str:
    """Get color for verdict display"""
    if verdict == Verdict.PRODUCTION_READY:
        return "green"
    elif verdict == Verdict.NOT_PRODUCTION_READY:
        return "red"
    elif verdict == Verdict.CONDITIONALLY_READY:
        return "yellow"
    return "white"


def format_verdict_emoji(verdict: Optional[Verdict]) -> str:
    """Get emoji for verdict display"""
    if verdict == Verdict.PRODUCTION_READY:
        return "[green]PASS[/green]"
    elif verdict == Verdict.NOT_PRODUCTION_READY:
        return "[red]FAIL[/red]"
    elif verdict == Verdict.CONDITIONALLY_READY:
        return "[yellow]WARN[/yellow]"
    return "[dim]--[/dim]"


def print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON"""
    console.print_json(json.dumps(data, indent=2, default=str))


def print_summary(result: AnalysisResult) -> None:
    """Print a brief summary of analysis results"""
    verdict_display = format_verdict_emoji(result.verdict)

    console.print()
    console.print(Panel(
        f"[bold]Analysis Complete[/bold]\n\n"
        f"Run ID: {result.run_id}\n"
        f"Verdict: {verdict_display}\n"
        f"Score: {result.score or 'N/A'}/100\n\n"
        f"Findings:\n"
        f"  [red]Blockers:[/red] {result.blocker_count}\n"
        f"  [yellow]Major:[/yellow] {result.major_count}\n"
        f"  [dim]Minor:[/dim] {result.minor_count}",
        title="ProdSensor Results",
        border_style=format_verdict_color(result.verdict)
    ))


def print_report_summary(report: Dict[str, Any]) -> None:
    """Print a summary of the full report"""
    verdict = report.get("verdict", "UNKNOWN")
    score = report.get("score")

    # Verdict panel
    verdict_color = "green" if verdict == "PRODUCTION_READY" else "red" if verdict == "NOT_PRODUCTION_READY" else "yellow"

    console.print()
    console.print(Panel(
        f"[bold]{verdict.replace('_', ' ')}[/bold]",
        title="Verdict",
        border_style=verdict_color,
        padding=(0, 2)
    ))

    if score is not None:
        console.print(f"\n[bold]Score:[/bold] {score}/100")

    # Dimensions table
    dimensions = report.get("dimensions", {})
    if dimensions:
        console.print("\n[bold]Dimension Scores[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Dimension")
        table.add_column("Score", justify="right")
        table.add_column("Status")

        for name, data in dimensions.items():
            dim_score = data.get("score", 0)
            status = "[green]PASS[/green]" if dim_score >= 70 else "[yellow]WARN[/yellow]" if dim_score >= 50 else "[red]FAIL[/red]"
            table.add_row(
                name.replace("_", " ").title(),
                str(dim_score),
                status
            )

        console.print(table)

    # Findings summary
    findings = report.get("findings", [])
    if findings:
        blockers = [f for f in findings if f.get("severity") == "Blocker"]
        majors = [f for f in findings if f.get("severity") == "Major"]
        minors = [f for f in findings if f.get("severity") == "Minor"]

        console.print(f"\n[bold]Findings Summary[/bold]")
        console.print(f"  [red]Blockers:[/red] {len(blockers)}")
        console.print(f"  [yellow]Major:[/yellow] {len(majors)}")
        console.print(f"  [dim]Minor:[/dim] {len(minors)}")

        # Show blockers detail
        if blockers:
            console.print("\n[bold red]Blockers (must fix):[/bold red]")
            for finding in blockers[:5]:  # Show first 5
                console.print(f"  - {finding.get('title', 'Untitled')}")
                if finding.get("description"):
                    console.print(f"    [dim]{finding['description'][:100]}...[/dim]")

            if len(blockers) > 5:
                console.print(f"  [dim]... and {len(blockers) - 5} more blockers[/dim]")


def print_markdown(report: Dict[str, Any]) -> None:
    """Print report as markdown"""
    verdict = report.get("verdict", "UNKNOWN")
    score = report.get("score", "N/A")

    md_content = f"""# Production Readiness Report

## Verdict: {verdict.replace('_', ' ')}

**Score:** {score}/100

## Dimension Scores

"""

    dimensions = report.get("dimensions", {})
    for name, data in dimensions.items():
        dim_score = data.get("score", 0)
        status = "PASS" if dim_score >= 70 else "WARN" if dim_score >= 50 else "FAIL"
        md_content += f"- **{name.replace('_', ' ').title()}**: {dim_score}/100 ({status})\n"

    findings = report.get("findings", [])
    blockers = [f for f in findings if f.get("severity") == "Blocker"]
    majors = [f for f in findings if f.get("severity") == "Major"]

    if blockers:
        md_content += "\n## Blockers (Must Fix)\n\n"
        for finding in blockers:
            md_content += f"### {finding.get('title', 'Untitled')}\n"
            md_content += f"{finding.get('description', '')}\n\n"

    if majors:
        md_content += "\n## Major Issues\n\n"
        for finding in majors[:10]:  # Limit to 10
            md_content += f"- **{finding.get('title', 'Untitled')}**: {finding.get('description', '')[:200]}\n"

    console.print(Markdown(md_content))


def print_progress(status: str, elapsed: float) -> None:
    """Print progress update during analysis"""
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    console.print(f"  Status: [cyan]{status}[/cyan] ({time_str})", end="\r")


def print_error(message: str) -> None:
    """Print an error message"""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message"""
    console.print(f"[green]{message}[/green]")


def print_warning(message: str) -> None:
    """Print a warning message"""
    console.print(f"[yellow]Warning:[/yellow] {message}")
