"""Main CLI application with Typer."""

from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from precogs_cli.config import config

# Initialize Typer app
app = typer.Typer(
    name="precogs",
    help="Precogs AI - Security-first code analysis CLI",
    add_completion=False,
)

console = Console()


def get_client():
    """Get Precogs client with configured API key."""
    from precogs import PrecogsClient, AuthenticationError

    api_key = config.api_key or os.environ.get("PRECOGS_API_KEY")
    if not api_key:
        console.print(
            "[red]Error:[/red] No API key configured. Run [bold]precogs auth login[/bold] first."
        )
        raise typer.Exit(1)

    try:
        return PrecogsClient(api_key=api_key)
    except (ValueError, AuthenticationError) as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# AUTH COMMANDS
# ============================================================================

auth_app = typer.Typer(help="Authentication commands")
app.add_typer(auth_app, name="auth")


@auth_app.command("login")
def auth_login(
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="API key (or enter interactively)"
    ),
):
    """Configure your Precogs API key."""
    if not api_key:
        api_key = typer.prompt("Enter your Precogs API key", hide_input=True)

    if not api_key.startswith("pk_"):
        console.print("[red]Error:[/red] Invalid API key format. Should start with 'pk_live_' or 'pk_test_'.")
        raise typer.Exit(1)

    # Validate the key by making a test request
    from precogs import PrecogsClient, AuthenticationError

    try:
        with PrecogsClient(api_key=api_key) as client:
            _ = client.projects.list()
    except AuthenticationError:
        console.print("[red]Error:[/red] Invalid API key. Please check and try again.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not validate key: {e}")

    config.api_key = api_key
    console.print("[green]✓[/green] API key saved to ~/.precogs/config.json")


@auth_app.command("logout")
def auth_logout():
    """Remove stored API key."""
    config.clear()
    console.print("[green]✓[/green] Logged out. API key removed.")


@auth_app.command("status")
def auth_status():
    """Show current authentication status."""
    if config.api_key:
        masked = config.api_key[:15] + "..." + config.api_key[-4:]
        console.print(f"[green]✓[/green] Authenticated with key: {masked}")
    else:
        console.print("[yellow]Not authenticated.[/yellow] Run [bold]precogs auth login[/bold]")


# ============================================================================
# PROJECTS COMMANDS
# ============================================================================

projects_app = typer.Typer(help="Manage projects")
app.add_typer(projects_app, name="projects")


@projects_app.command("list")
def projects_list():
    """List all projects."""
    client = get_client()

    with console.status("Fetching projects..."):
        try:
            projects = client.projects.list()
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        return

    table = Table(title="Projects")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Provider")
    table.add_column("Branch")
    table.add_column("Last Scan")

    for p in projects:
        table.add_row(
            p.get("id", p.get("_id", "N/A")),
            p.get("name", "Unknown"),
            p.get("provider", "N/A"),
            p.get("branch", "main"),
            p.get("lastScan", "Never"),
        )

    console.print(table)


@projects_app.command("get")
def projects_get(project_id: str = typer.Argument(..., help="Project ID")):
    """Get project details."""
    client = get_client()

    with console.status("Fetching project..."):
        try:
            project = client.projects.get(project_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(Panel.fit(
        f"[bold]{project.get('name', 'Unknown')}[/bold]\n\n"
        f"ID: {project.get('id', project.get('_id', 'N/A'))}\n"
        f"Provider: {project.get('provider', 'N/A')}\n"
        f"Repository: {project.get('repoUrl', 'N/A')}\n"
        f"Branch: {project.get('branch', 'main')}\n"
        f"Created: {project.get('createdAt', 'N/A')}",
        title="Project Details"
    ))


# ============================================================================
# SCAN COMMANDS
# ============================================================================

scan_app = typer.Typer(help="Trigger security scans")
app.add_typer(scan_app, name="scan")


@scan_app.command("code")
def scan_code(
    project_id: str = typer.Argument(..., help="Project ID to scan"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to scan"),
):
    """Trigger a code security scan (SAST)."""
    client = get_client()

    with console.status("[bold green]Starting code scan...[/bold green]"):
        try:
            result = client.scans.trigger_code_scan(project_id, branch)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Scan started: {result.get('scanId', result.get('id', 'N/A'))}")
    console.print(f"  Status: {result.get('status', 'pending')}")


@scan_app.command("dependency")
def scan_dependency(project_id: str = typer.Argument(..., help="Project ID")):
    """Trigger a dependency scan (SCA)."""
    client = get_client()

    with console.status("[bold green]Starting dependency scan...[/bold green]"):
        try:
            result = client.scans.trigger_dependency_scan(project_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Dependency scan started: {result.get('scanId', 'N/A')}")


@scan_app.command("iac")
def scan_iac(project_id: str = typer.Argument(..., help="Project ID")):
    """Trigger an Infrastructure as Code scan."""
    client = get_client()

    with console.status("[bold green]Starting IaC scan...[/bold green]"):
        try:
            result = client.scans.trigger_iac_scan(project_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] IaC scan started: {result.get('scanId', 'N/A')}")


@scan_app.command("container")
def scan_container(
    project_id: str = typer.Argument(..., help="Project ID"),
    image: str = typer.Argument(..., help="Container image (e.g., nginx:latest)"),
):
    """Trigger a container image scan."""
    client = get_client()

    with console.status(f"[bold green]Scanning {image}...[/bold green]"):
        try:
            result = client.scans.trigger_container_scan(project_id, image)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Container scan started: {result.get('scanId', 'N/A')}")


# ============================================================================
# VULNERABILITIES COMMANDS  
# ============================================================================

vulns_app = typer.Typer(help="View and manage vulnerabilities")
app.add_typer(vulns_app, name="vulns")


@vulns_app.command("list")
def vulns_list(
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project"),
    severity: Optional[str] = typer.Option(None, "--severity", "-s", help="Filter by severity"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
):
    """List vulnerabilities."""
    client = get_client()

    with console.status("Fetching vulnerabilities..."):
        try:
            vulns = client.vulnerabilities.list(
                project_id=project_id,
                severity=severity,
                limit=limit,
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    if not vulns:
        console.print("[green]No vulnerabilities found![/green]")
        return

    table = Table(title=f"Vulnerabilities ({len(vulns)} found)")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Severity", width=10)
    table.add_column("Title", no_wrap=False)
    table.add_column("File", style="dim")

    severity_colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
    }

    for v in vulns:
        sev = v.get("severity", "unknown").lower()
        table.add_row(
            v.get("id", v.get("_id", "N/A"))[:12],
            f"[{severity_colors.get(sev, 'white')}]{sev.upper()}[/]",
            v.get("title", v.get("message", "Unknown")),
            v.get("file", v.get("filePath", "N/A")),
        )

    console.print(table)


@vulns_app.command("get")
def vulns_get(vuln_id: str = typer.Argument(..., help="Vulnerability ID")):
    """Get vulnerability details."""
    client = get_client()

    with console.status("Fetching vulnerability..."):
        try:
            vuln = client.vulnerabilities.get(vuln_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    sev = vuln.get("severity", "unknown").upper()
    console.print(Panel.fit(
        f"[bold]{vuln.get('title', 'Unknown')}[/bold]\n\n"
        f"Severity: {sev}\n"
        f"File: {vuln.get('file', vuln.get('filePath', 'N/A'))}\n"
        f"Line: {vuln.get('line', vuln.get('startLine', 'N/A'))}\n\n"
        f"[dim]{vuln.get('description', 'No description')}[/dim]",
        title="Vulnerability Details"
    ))


@vulns_app.command("fix")
def vulns_fix(vuln_id: str = typer.Argument(..., help="Vulnerability ID")):
    """Get AI-generated fix suggestion."""
    client = get_client()

    with console.status("[bold magenta]Generating AI fix...[/bold magenta]"):
        try:
            fix = client.vulnerabilities.get_ai_fix(vuln_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(Panel(
        fix.get("suggestedCode", fix.get("fix", "No fix available")),
        title="[bold green]AI-Generated Fix[/bold green]",
        border_style="green",
    ))


# ============================================================================
# DASHBOARD COMMANDS
# ============================================================================

@app.command("dashboard")
def dashboard(
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project"),
):
    """Show security dashboard overview."""
    client = get_client()

    with console.status("Fetching dashboard data..."):
        try:
            overview = client.dashboard.get_overview(project_id)
            distribution = client.dashboard.get_severity_distribution(project_id)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print("\n[bold]Security Dashboard[/bold]\n")

    # Overview stats
    stats = overview.get("stats", overview)
    console.print(f"  Total Vulnerabilities: {stats.get('total', 0)}")
    console.print(f"  Critical: [red]{stats.get('critical', 0)}[/red]")
    console.print(f"  High: [red]{stats.get('high', 0)}[/red]")
    console.print(f"  Medium: [yellow]{stats.get('medium', 0)}[/yellow]")
    console.print(f"  Low: [blue]{stats.get('low', 0)}[/blue]")
    console.print()


# ============================================================================
# VERSION
# ============================================================================

@app.command("version")
def version():
    """Show CLI version."""
    from precogs_cli import __version__
    console.print(f"Precogs CLI v{__version__}")


if __name__ == "__main__":
    app()
