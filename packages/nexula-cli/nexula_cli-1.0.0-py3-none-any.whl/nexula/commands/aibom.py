import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..config import config
from ..api_client import APIClient, APIError

console = Console()


@click.group()
def aibom():
    """AIBOM (AI Bill of Materials) commands"""
    pass


@aibom.command()
@click.option("--project-id", type=int, help="Project ID (overrides .nexula.yaml)")
def generate(project_id: int):
    """Generate AIBOM for your AI/ML project"""
    try:
        client = APIClient()
        
        # Get project ID
        if not project_id:
            project_id = config.get_project_id()
            if not project_id:
                console.print("[red]✗[/red] No project configured. Run [bold]nexula init[/bold] first.")
                raise click.Abort()
        
        console.print(f"[blue]ℹ[/blue] Generating AIBOM for project ID: {project_id}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating AIBOM...", total=None)
            
            result = client.generate_aibom(project_id)
            
            progress.update(task, completed=True)
        
        console.print(Panel.fit(
            f"[green]✓[/green] AIBOM generation started\n\n"
            f"AIBOM ID: [bold]{result['id']}[/bold]\n"
            f"Status: [bold]{result.get('status', 'pending')}[/bold]\n\n"
            f"Check status with:\n"
            f"  [bold]nexula aibom view {result['id']}[/bold]",
            title="[green]AIBOM Generation Started[/green]",
            border_style="green"
        ))
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@aibom.command()
@click.option("--project-id", type=int, help="Project ID")
def list(project_id: int):
    """List AIBOMs for project"""
    try:
        client = APIClient()
        
        if not project_id:
            project_id = config.get_project_id()
            if not project_id:
                console.print("[red]✗[/red] No project configured. Run [bold]nexula init[/bold] first.")
                raise click.Abort()
        
        aiboms = client.list_aiboms(project_id)
        
        if not aiboms:
            console.print("[yellow]![/yellow] No AIBOMs found. Generate one with [bold]nexula aibom generate[/bold]")
            return
        
        table = Table(title=f"AIBOMs for Project {project_id}")
        table.add_column("ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Assets", justify="right")
        table.add_column("Status")
        
        for aibom in aiboms:
            table.add_row(
                str(aibom["id"]),
                aibom.get("created_at", "N/A"),
                str(aibom.get("asset_count", 0)),
                aibom.get("status", "unknown")
            )
        
        console.print(table)
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@aibom.command()
@click.argument("aibom_id", type=int)
def view(aibom_id: int):
    """View AIBOM details"""
    try:
        client = APIClient()
        aibom = client.get_aibom(aibom_id)
        
        console.print(Panel.fit(
            f"AIBOM ID: [bold]{aibom['id']}[/bold]\n"
            f"Project ID: {aibom.get('project_id', 'N/A')}\n"
            f"Created: {aibom.get('created_at', 'N/A')}\n"
            f"Assets: [bold]{aibom.get('asset_count', 0)}[/bold]\n"
            f"Status: {aibom.get('status', 'unknown')}",
            title="[blue]AIBOM Details[/blue]",
            border_style="blue"
        ))
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()
