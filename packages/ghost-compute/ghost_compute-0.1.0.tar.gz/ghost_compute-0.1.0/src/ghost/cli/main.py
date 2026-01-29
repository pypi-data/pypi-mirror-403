"""
Ghost Compute CLI.

Command-line interface for Ghost cluster optimization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ghost import __version__
from ghost.core.client import GhostClient
from ghost.core.config import GhostConfig
from ghost.core.models import Platform, ClusterStatus

app = typer.Typer(
    name="ghost",
    help="Ghost Compute - Intelligent Serverless Orchestration for Data Platforms",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"Ghost Compute v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit"
    ),
) -> None:
    """Ghost Compute - Eliminate idle cluster waste and cold start latency."""
    pass


@app.command()
def platforms() -> None:
    """Show supported platforms and their requirements."""
    console.print("\n[bold]Supported Platforms[/bold]\n")

    platforms_info = [
        {
            "name": "Databricks",
            "id": "databricks",
            "auth": "Personal Access Token",
            "requirements": "Workspace URL and PAT",
            "features": "Full support: Predict, Hibernate, Spot, Pool, Insight",
        },
        {
            "name": "AWS EMR",
            "id": "emr",
            "auth": "AWS Credentials (Profile/IAM)",
            "requirements": "AWS profile and region",
            "features": "Full support: Predict, Hibernate (terminate), Spot, Pool, Insight",
        },
        {
            "name": "Azure Synapse",
            "id": "synapse",
            "auth": "Azure DefaultCredential",
            "requirements": "Subscription ID, optional resource group",
            "features": "Full support: Predict, Hibernate (auto-pause), Pool, Insight",
        },
        {
            "name": "Google Dataproc",
            "id": "dataproc",
            "auth": "Google Cloud Application Default Credentials",
            "requirements": "Project ID and region",
            "features": "Full support: Predict, Hibernate (delete), Preemptible VMs, Pool, Insight",
        },
    ]

    table = Table(title="Ghost Compute Platforms")
    table.add_column("Platform", style="cyan", no_wrap=True)
    table.add_column("ID", style="dim")
    table.add_column("Authentication", style="yellow")
    table.add_column("Requirements", style="white")

    for p in platforms_info:
        table.add_row(p["name"], p["id"], p["auth"], p["requirements"])

    console.print(table)

    console.print("\n[bold]Connection Examples:[/bold]\n")
    console.print("  [cyan]Databricks:[/cyan]")
    console.print("    ghost connect databricks --workspace-url https://xxx.cloud.databricks.com --token dapi...\n")
    console.print("  [cyan]AWS EMR:[/cyan]")
    console.print("    ghost connect emr --profile default --region us-east-1\n")
    console.print("  [cyan]Azure Synapse:[/cyan]")
    console.print("    ghost connect synapse --subscription-id xxxx-xxxx --resource-group my-rg\n")
    console.print("  [cyan]Google Dataproc:[/cyan]")
    console.print("    ghost connect dataproc --project-id my-project --region us-central1\n")


@app.command()
def connect(
    platform: str = typer.Argument(..., help="Platform to connect to (databricks, emr, synapse, dataproc)"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL (Databricks)"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token (Databricks)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile name (EMR)"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Cloud region (EMR/Dataproc)"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", help="Azure subscription ID (Synapse)"),
    resource_group: Optional[str] = typer.Option(None, "--resource-group", help="Azure resource group (Synapse)"),
    project_id: Optional[str] = typer.Option(None, "--project-id", help="GCP project ID (Dataproc)"),
) -> None:
    """Connect Ghost to a data platform."""
    platform = platform.lower()
    valid_platforms = ["databricks", "emr", "synapse", "dataproc"]

    if platform not in valid_platforms:
        console.print(f"[red]Invalid platform: {platform}[/red]")
        console.print(f"Valid platforms: {', '.join(valid_platforms)}")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Connecting to {platform.upper()}...[/bold blue]\n")

    # Create credentials directory
    creds_dir = Path.home() / ".ghost"
    creds_dir.mkdir(exist_ok=True)
    creds_file = creds_dir / "credentials.json"

    # Load existing credentials
    if creds_file.exists():
        with open(creds_file) as f:
            creds = json.load(f)
    else:
        creds = {}

    # Prompt for missing values based on platform
    if platform == "databricks":
        if not workspace_url:
            workspace_url = typer.prompt("Workspace URL")
        if not token:
            token = typer.prompt("Personal Access Token", hide_input=True)

        creds["databricks"] = {
            "host": workspace_url,
            "token": token,
        }
        console.print("[dim]Using Databricks personal access token authentication[/dim]")

    elif platform == "emr":
        if not profile:
            profile = typer.prompt("AWS Profile", default="default")
        if not region:
            region = typer.prompt("AWS Region", default="us-east-1")

        creds["emr"] = {
            "profile": profile,
            "region": region,
        }
        console.print("[dim]Using AWS credentials from profile[/dim]")
        console.print(f"[dim]Region: {region}[/dim]")

    elif platform == "synapse":
        if not subscription_id:
            subscription_id = typer.prompt("Azure Subscription ID")
        if not resource_group:
            resource_group = typer.prompt("Resource Group (optional, press Enter to skip)", default="")

        creds["synapse"] = {
            "subscription_id": subscription_id,
            "resource_group": resource_group if resource_group else None,
        }
        console.print("[dim]Using Azure DefaultAzureCredential[/dim]")
        console.print("[dim]Ensure you're logged in via 'az login' or have environment credentials set[/dim]")

    elif platform == "dataproc":
        if not project_id:
            project_id = typer.prompt("GCP Project ID")
        if not region:
            region = typer.prompt("GCP Region", default="us-central1")

        creds["dataproc"] = {
            "project_id": project_id,
            "region": region,
        }
        console.print("[dim]Using Google Cloud default credentials[/dim]")
        console.print("[dim]Ensure you're logged in via 'gcloud auth application-default login'[/dim]")

    # Save credentials
    with open(creds_file, "w") as f:
        json.dump(creds, f, indent=2)
    creds_file.chmod(0o600)

    # Test connection
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Testing connection...", total=None)

        try:
            # Build platform config based on credentials
            platform_config = creds.get(platform, {})
            client = GhostClient(
                platform=platform,
                workspace_url=workspace_url,
                platform_config=platform_config,
            )
            client.connect()
            console.print("\n[bold green]✓ Successfully connected![/bold green]")
            console.print(f"Credentials saved to {creds_file}\n")
        except Exception as e:
            console.print(f"\n[bold red]✗ Connection failed: {e}[/bold red]\n")
            raise typer.Exit(1)


@app.command()
def analyze(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform to analyze"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for analysis (JSON)"),
) -> None:
    """Analyze current cluster usage and potential savings."""
    console.print("\n[bold blue]Analyzing workspace...[/bold blue]\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Connecting to platform...", total=None)

        client = GhostClient(platform=platform, workspace_url=workspace_url)
        client.connect()

        progress.update(task, description="Analyzing clusters...")
        analysis = client.analyze(output_path=output)

    # Display summary
    summary = analysis["summary"]
    costs = analysis["costs"]
    potential = analysis["optimization_potential"]

    console.print(Panel.fit(
        f"""[bold]Workspace Analysis[/bold]

[cyan]Clusters:[/cyan]
  Total: {summary['total_clusters']}
  Running: {summary['running_clusters']}
  Idle: {summary['idle_clusters']}
  Terminated: {summary['terminated_clusters']}

[cyan]Current Costs:[/cyan]
  Hourly: ${costs['total_hourly_usd']:.2f}
  Idle Waste: ${costs['idle_hourly_usd']:.2f}/hr ({costs['waste_percentage']:.1f}%)
  Est. Monthly: ${costs['estimated_monthly_usd']:,.2f}

[green]Optimization Potential:[/green]
  Monthly Savings: ${potential['monthly_savings_usd']:,.2f}
  Annual Savings: ${potential['annual_savings_usd']:,.2f}
  Insights Found: {potential['insights_count']}""",
        title="Ghost Analysis",
        border_style="blue",
    ))

    # Display insights
    if analysis["insights"]:
        console.print("\n[bold]Top Optimization Insights:[/bold]\n")
        for i, insight in enumerate(analysis["insights"][:5], 1):
            severity_color = {"high": "red", "medium": "yellow", "low": "green"}.get(insight["severity"], "white")
            console.print(f"  {i}. [{severity_color}][{insight['severity'].upper()}][/{severity_color}] {insight['title']}")
            console.print(f"     Potential Savings: [green]${insight['monthly_savings_usd']:,.2f}/month[/green]\n")

    if output:
        console.print(f"\n[dim]Full analysis saved to {output}[/dim]")

    console.print()


@app.command()
def optimize(
    strategies: str = typer.Option("predict,hibernate,spot", "--strategies", "-s", help="Strategies to enable (comma-separated)"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
    target_savings: float = typer.Option(0.40, "--target", "-t", help="Target savings percentage (0.0-1.0)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Don't make changes, just report"),
) -> None:
    """Enable Ghost optimization for your clusters."""
    strategy_list = [s.strip() for s in strategies.split(",")]

    console.print(f"\n[bold blue]Enabling Ghost optimization...[/bold blue]")
    console.print(f"Strategies: {', '.join(strategy_list)}")
    console.print(f"Target savings: {target_savings*100:.0f}%")
    if dry_run:
        console.print("[yellow]DRY RUN - no changes will be made[/yellow]")
    console.print()

    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.optimize(strategies=strategy_list, target_savings=target_savings, dry_run=dry_run)

    console.print("[bold green]✓ Ghost optimization enabled![/bold green]")
    console.print("\nMonitor status with: [cyan]ghost status[/cyan]")
    console.print("View savings with: [cyan]ghost stats[/cyan]\n")


@app.command()
def clusters(
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    ghost_managed: Optional[bool] = typer.Option(None, "--managed", "-m", help="Filter by Ghost management"),
) -> None:
    """List clusters and their status."""
    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.connect()

    status_filter = ClusterStatus(status) if status else None
    cluster_list = client.get_clusters(status=status_filter, ghost_managed=ghost_managed)

    table = Table(title="Clusters")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Workers", justify="right")
    table.add_column("Cost/hr", justify="right", style="green")
    table.add_column("Ghost", justify="center")

    status_colors = {
        ClusterStatus.RUNNING: "green",
        ClusterStatus.IDLE: "yellow",
        ClusterStatus.HIBERNATED: "blue",
        ClusterStatus.TERMINATED: "dim",
        ClusterStatus.ERROR: "red",
    }

    for cluster in cluster_list:
        color = status_colors.get(cluster.status, "white")
        ghost_status = "✓" if cluster.ghost_managed else ""
        table.add_row(
            cluster.cluster_id[:12] + "...",
            cluster.cluster_name[:30],
            f"[{color}]{cluster.status.value}[/{color}]",
            str(cluster.num_workers),
            f"${cluster.hourly_cost_usd:.2f}",
            ghost_status,
        )

    console.print()
    console.print(table)
    console.print()


@app.command()
def stats(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to include"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
) -> None:
    """Show optimization statistics and savings."""
    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.connect()

    stats = client.get_stats(period_days=days)

    console.print(Panel.fit(
        f"""[bold]Ghost Optimization Statistics[/bold]
[dim]Last {days} days[/dim]

[cyan]Clusters:[/cyan]
  Total: {stats.total_clusters}
  Ghost Managed: {stats.ghost_managed_clusters}
  Active: {stats.active_clusters}
  Hibernated: {stats.hibernated_clusters}

[cyan]Cost Savings:[/cyan]
  Total Spend: ${stats.total_spend_usd:,.2f}
  Savings: [green]${stats.savings_usd:,.2f}[/green] ({stats.savings_percentage:.1f}%)
  Projected Monthly: [green]${stats.projected_monthly_savings_usd:,.2f}[/green]

[cyan]Performance:[/cyan]
  Cold Starts Prevented: {stats.cold_starts_prevented}
  Avg. Utilization: {stats.average_utilization_percent:.1f}%""",
        title="Ghost Stats",
        border_style="green",
    ))
    console.print()


@app.command()
def insights(
    min_savings: float = typer.Option(0, "--min-savings", "-m", help="Minimum monthly savings to show"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
) -> None:
    """Show cost optimization insights and recommendations."""
    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.connect()

    insight_list = client.get_insights(min_savings_usd=min_savings)

    if not insight_list:
        console.print("\n[green]No optimization insights found - your infrastructure looks good![/green]\n")
        return

    console.print(f"\n[bold]Found {len(insight_list)} optimization insights:[/bold]\n")

    for insight in insight_list:
        severity_color = {"high": "red", "medium": "yellow", "low": "green", "critical": "bold red"}.get(insight.severity, "white")

        console.print(Panel(
            f"""[{severity_color}][{insight.severity.upper()}][/{severity_color}] {insight.title}

{insight.description}

[cyan]Recommendation:[/cyan] {insight.recommendation}

[green]Potential Savings:[/green]
  Monthly: ${insight.estimated_monthly_savings_usd:,.2f}
  Annual: ${insight.estimated_annual_savings_usd:,.2f}

[dim]Affected clusters: {len(insight.affected_clusters)}[/dim]""",
            border_style=severity_color,
        ))
        console.print()


@app.command()
def hibernate(
    cluster_id: str = typer.Argument(..., help="Cluster ID to hibernate"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
) -> None:
    """Hibernate a specific cluster."""
    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.connect()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(f"Hibernating cluster {cluster_id}...", total=None)
        result = client.hibernate_cluster(cluster_id)

    if result.success:
        console.print(f"\n[bold green]✓ {result.message}[/bold green]")
        console.print(f"Estimated daily savings: [green]${result.estimated_savings_usd:.2f}[/green]\n")
    else:
        console.print(f"\n[bold red]✗ {result.message}[/bold red]")
        if result.error:
            console.print(f"Error: {result.error}\n")
        raise typer.Exit(1)


@app.command()
def resume(
    cluster_id: str = typer.Argument(..., help="Cluster ID to resume"),
    platform: Optional[str] = typer.Option(None, "--platform", "-p", help="Platform"),
    workspace_url: Optional[str] = typer.Option(None, "--workspace-url", "-w", help="Workspace URL"),
) -> None:
    """Resume a hibernated cluster."""
    client = GhostClient(platform=platform, workspace_url=workspace_url)
    client.connect()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(f"Resuming cluster {cluster_id}...", total=None)
        result = client.resume_cluster(cluster_id)

    if result.success:
        console.print(f"\n[bold green]✓ {result.message}[/bold green]")
        if result.cold_start_prevented:
            console.print("[cyan]Cold start prevented using cached state![/cyan]\n")
    else:
        console.print(f"\n[bold red]✗ {result.message}[/bold red]")
        if result.error:
            console.print(f"Error: {result.error}\n")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
