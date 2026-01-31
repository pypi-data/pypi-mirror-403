"""
ProdSensor CLI - Command Line Interface
"""

import sys
import click
from typing import Optional

from prodsensor import __version__
from prodsensor.client import (
    ProdSensorClient,
    AnalysisResult,
    Verdict,
    ApiError,
    AuthError,
    RateLimitError,
)
from prodsensor.formatters import (
    console,
    print_json,
    print_summary,
    print_report_summary,
    print_markdown,
    print_progress,
    print_error,
    print_success,
    print_warning,
)


# Exit codes for CI/CD
EXIT_PRODUCTION_READY = 0
EXIT_NOT_PRODUCTION_READY = 1
EXIT_CONDITIONALLY_READY = 2
EXIT_API_ERROR = 3
EXIT_AUTH_ERROR = 4
EXIT_TIMEOUT = 5


def get_exit_code(result: AnalysisResult) -> int:
    """Get exit code based on analysis result"""
    if result.verdict == Verdict.PRODUCTION_READY:
        return EXIT_PRODUCTION_READY
    elif result.verdict == Verdict.NOT_PRODUCTION_READY:
        return EXIT_NOT_PRODUCTION_READY
    elif result.verdict == Verdict.CONDITIONALLY_READY:
        return EXIT_CONDITIONALLY_READY
    # Default to not ready if no verdict
    return EXIT_NOT_PRODUCTION_READY


@click.group()
@click.version_option(version=__version__, prog_name="prodsensor")
def main():
    """ProdSensor CLI - Production Readiness Analysis

    Analyze your codebase for production readiness across 8 dimensions:
    Scalability, Security, Reliability, Performance, Observability,
    Testability, Architecture, and Maintainability.

    \b
    Exit Codes:
      0 - PRODUCTION_READY
      1 - NOT_PRODUCTION_READY
      2 - CONDITIONALLY_READY
      3 - API/Network error
      4 - Authentication error
      5 - Timeout

    \b
    Examples:
      prodsensor analyze https://github.com/owner/repo
      prodsensor status abc123
      prodsensor report abc123 --format json
    """
    pass


@main.command()
@click.argument("target")
@click.option(
    "--api-key", "-k",
    envvar="PRODSENSOR_API_KEY",
    help="API key (or set PRODSENSOR_API_KEY env var)"
)
@click.option(
    "--api-url",
    envvar="PRODSENSOR_API_URL",
    help="API URL (default: production)"
)
@click.option(
    "--timeout", "-t",
    default=600,
    type=int,
    help="Max time to wait for analysis (seconds)"
)
@click.option(
    "--poll-interval",
    default=5,
    type=int,
    help="Seconds between status checks"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["summary", "json", "markdown"]),
    default="summary",
    help="Output format"
)
@click.option(
    "--no-wait", "-n",
    is_flag=True,
    help="Start analysis and return immediately (don't wait for completion)"
)
@click.option(
    "--fail-on",
    type=click.Choice(["not-ready", "blockers", "never"]),
    default="not-ready",
    help="When to return non-zero exit code"
)
def analyze(
    target: str,
    api_key: Optional[str],
    api_url: Optional[str],
    timeout: int,
    poll_interval: int,
    format: str,
    no_wait: bool,
    fail_on: str
):
    """Analyze a repository for production readiness.

    TARGET can be a GitHub repository URL.

    \b
    Examples:
      prodsensor analyze https://github.com/owner/repo
      prodsensor analyze https://github.com/owner/repo --format json
      prodsensor analyze https://github.com/owner/repo --no-wait
    """
    try:
        client = ProdSensorClient(api_key=api_key, api_url=api_url)

        console.print(f"\n[bold]Starting analysis of:[/bold] {target}")

        if no_wait:
            # Start and return immediately
            run_id = client.analyze_repo(target)
            console.print(f"\nAnalysis started. Run ID: [cyan]{run_id}[/cyan]")
            console.print(f"\nCheck status with: [dim]prodsensor status {run_id}[/dim]")
            console.print(f"Get report with:   [dim]prodsensor report {run_id}[/dim]")
            sys.exit(EXIT_PRODUCTION_READY)

        # Start and wait for completion
        console.print("\nAnalyzing... (this may take a few minutes)")

        def progress(status, elapsed):
            print_progress(status.value, elapsed)

        result = client.analyze_and_wait(
            target,
            timeout=timeout,
            poll_interval=poll_interval,
            progress_callback=progress
        )

        console.print()  # Clear progress line

        if result.error:
            print_error(f"Analysis failed: {result.error}")
            sys.exit(EXIT_API_ERROR)

        # Output results
        if format == "json":
            report = client.get_report(result.run_id)
            print_json(report)
        elif format == "markdown":
            report = client.get_report(result.run_id)
            print_markdown(report)
        else:
            print_summary(result)

        # Determine exit code based on fail-on setting
        if fail_on == "never":
            sys.exit(EXIT_PRODUCTION_READY)
        elif fail_on == "blockers":
            if result.blocker_count > 0:
                sys.exit(EXIT_NOT_PRODUCTION_READY)
            sys.exit(EXIT_PRODUCTION_READY)
        else:  # not-ready (default)
            sys.exit(get_exit_code(result))

    except AuthError as e:
        print_error(f"Authentication failed: {e.message}")
        console.print("\n[dim]Set your API key with:[/dim]")
        console.print("  prodsensor config set-key YOUR_API_KEY")
        console.print("  [dim]or[/dim]")
        console.print("  export PRODSENSOR_API_KEY=YOUR_API_KEY")
        sys.exit(EXIT_AUTH_ERROR)

    except RateLimitError as e:
        print_error(f"Rate limit exceeded. Retry after {e.retry_after} seconds.")
        sys.exit(EXIT_API_ERROR)

    except TimeoutError:
        print_error(f"Analysis timed out after {timeout} seconds.")
        console.print("[dim]Try increasing --timeout or using --no-wait[/dim]")
        sys.exit(EXIT_TIMEOUT)

    except ApiError as e:
        print_error(f"API error: {e.message}")
        sys.exit(EXIT_API_ERROR)

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(EXIT_API_ERROR)


@main.command()
@click.argument("run_id")
@click.option(
    "--api-key", "-k",
    envvar="PRODSENSOR_API_KEY",
    help="API key (or set PRODSENSOR_API_KEY env var)"
)
@click.option(
    "--api-url",
    envvar="PRODSENSOR_API_URL",
    help="API URL (default: production)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["summary", "json"]),
    default="summary",
    help="Output format"
)
def status(run_id: str, api_key: Optional[str], api_url: Optional[str], format: str):
    """Check the status of an analysis run.

    \b
    Examples:
      prodsensor status abc123
      prodsensor status abc123 --format json
    """
    try:
        client = ProdSensorClient(api_key=api_key, api_url=api_url)
        result = client.get_run_status(run_id)

        if format == "json":
            print_json({
                "run_id": result.run_id,
                "status": result.status.value,
                "verdict": result.verdict.value if result.verdict else None,
                "score": result.score,
                "blocker_count": result.blocker_count,
                "major_count": result.major_count,
                "minor_count": result.minor_count,
                "error": result.error
            })
        else:
            console.print(f"\n[bold]Run ID:[/bold] {result.run_id}")
            console.print(f"[bold]Status:[/bold] {result.status.value}")

            if result.verdict:
                color = "green" if result.verdict == Verdict.PRODUCTION_READY else "red" if result.verdict == Verdict.NOT_PRODUCTION_READY else "yellow"
                console.print(f"[bold]Verdict:[/bold] [{color}]{result.verdict.value}[/{color}]")

            if result.score is not None:
                console.print(f"[bold]Score:[/bold] {result.score}/100")

            if result.error:
                print_error(result.error)

        sys.exit(get_exit_code(result) if result.verdict else EXIT_PRODUCTION_READY)

    except AuthError as e:
        print_error(f"Authentication failed: {e.message}")
        sys.exit(EXIT_AUTH_ERROR)

    except ApiError as e:
        print_error(f"API error: {e.message}")
        sys.exit(EXIT_API_ERROR)


@main.command()
@click.argument("run_id")
@click.option(
    "--api-key", "-k",
    envvar="PRODSENSOR_API_KEY",
    help="API key (or set PRODSENSOR_API_KEY env var)"
)
@click.option(
    "--api-url",
    envvar="PRODSENSOR_API_URL",
    help="API URL (default: production)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["summary", "json", "markdown"]),
    default="summary",
    help="Output format"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Write output to file instead of stdout"
)
def report(
    run_id: str,
    api_key: Optional[str],
    api_url: Optional[str],
    format: str,
    output: Optional[str]
):
    """Get the full analysis report.

    \b
    Examples:
      prodsensor report abc123
      prodsensor report abc123 --format json
      prodsensor report abc123 --format json -o report.json
    """
    try:
        client = ProdSensorClient(api_key=api_key, api_url=api_url)
        report_data = client.get_report(run_id)

        if output:
            import json
            with open(output, "w") as f:
                if format == "json":
                    json.dump(report_data, f, indent=2, default=str)
                else:
                    # For summary/markdown, still write JSON for file output
                    json.dump(report_data, f, indent=2, default=str)
            print_success(f"Report saved to {output}")
        else:
            if format == "json":
                print_json(report_data)
            elif format == "markdown":
                print_markdown(report_data)
            else:
                print_report_summary(report_data)

        # Exit based on verdict
        verdict = report_data.get("verdict")
        if verdict == "PRODUCTION_READY":
            sys.exit(EXIT_PRODUCTION_READY)
        elif verdict == "NOT_PRODUCTION_READY":
            sys.exit(EXIT_NOT_PRODUCTION_READY)
        elif verdict == "CONDITIONALLY_READY":
            sys.exit(EXIT_CONDITIONALLY_READY)
        else:
            sys.exit(EXIT_PRODUCTION_READY)

    except AuthError as e:
        print_error(f"Authentication failed: {e.message}")
        sys.exit(EXIT_AUTH_ERROR)

    except ApiError as e:
        print_error(f"API error: {e.message}")
        sys.exit(EXIT_API_ERROR)


@main.group()
def config():
    """Manage CLI configuration."""
    pass


@config.command("set-key")
@click.argument("api_key")
def set_key(api_key: str):
    """Save your API key for future use.

    The key is stored in ~/.prodsensor/config with restricted permissions.

    \b
    Example:
      prodsensor config set-key ps_live_abc123...
    """
    if not api_key.startswith("ps_live_"):
        print_warning("API key should start with 'ps_live_'")

    ProdSensorClient.save_api_key(api_key)
    print_success("API key saved successfully")
    console.print(f"[dim]Stored in: {ProdSensorClient.CONFIG_FILE}[/dim]")


@config.command("clear-key")
def clear_key():
    """Remove your saved API key."""
    ProdSensorClient.clear_api_key()
    print_success("API key removed")


@config.command("show")
def show_config():
    """Show current configuration."""
    console.print("\n[bold]ProdSensor CLI Configuration[/bold]\n")

    # Check for API key
    import os
    env_key = os.getenv("PRODSENSOR_API_KEY")
    if env_key:
        console.print(f"[bold]API Key:[/bold] [green]Set via PRODSENSOR_API_KEY[/green]")
        console.print(f"  [dim]{env_key[:12]}...{env_key[-4:]}[/dim]")
    elif ProdSensorClient.CONFIG_FILE.exists():
        client = ProdSensorClient()
        if client.api_key:
            console.print(f"[bold]API Key:[/bold] [green]Set via config file[/green]")
            console.print(f"  [dim]{client.api_key[:12]}...{client.api_key[-4:]}[/dim]")
        else:
            console.print(f"[bold]API Key:[/bold] [red]Not set[/red]")
    else:
        console.print(f"[bold]API Key:[/bold] [red]Not set[/red]")

    # API URL
    api_url = os.getenv("PRODSENSOR_API_URL", ProdSensorClient.DEFAULT_API_URL)
    console.print(f"\n[bold]API URL:[/bold] {api_url}")

    # Config file location
    console.print(f"\n[bold]Config file:[/bold] {ProdSensorClient.CONFIG_FILE}")
    if ProdSensorClient.CONFIG_FILE.exists():
        console.print("  [green]exists[/green]")
    else:
        console.print("  [dim]not created[/dim]")


if __name__ == "__main__":
    main()
