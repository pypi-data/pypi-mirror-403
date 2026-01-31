import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from ..config import config
from ..api_client import APIClient, APIError

console = Console()


@click.command()
@click.option("--workspace-id", type=int, help="Workspace ID")
@click.option("--project-id", type=int, help="Project ID")
@click.option("--create", is_flag=True, help="Create new project")
def init(workspace_id: int, project_id: int, create: bool):
    """Initialize Nexula project in current directory"""
    try:
        client = APIClient()
        
        # Select workspace
        if not workspace_id:
            workspaces = client.list_workspaces()
            if not workspaces:
                console.print("[red]✗[/red] No workspaces found. Create one in the dashboard first.")
                raise click.Abort()
            
            table = Table(title="Available Workspaces")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description")
            
            for ws in workspaces:
                table.add_row(str(ws["id"]), ws["workspace_name"], ws.get("details", ""))
            
            console.print(table)
            workspace_id = int(Prompt.ask("Select workspace ID"))
        
        # Create or select project
        if create:
            name = Prompt.ask("Project name")
            description = Prompt.ask("Description", default="")
            repo_url = Prompt.ask("Repository URL", default="")
            
            project = client.create_project(workspace_id, name, description, repo_url)
            project_id = project["id"]
            console.print(f"[green]✓[/green] Created project: {name}")
        
        elif not project_id:
            projects = client.list_projects(workspace_id)
            if not projects:
                if Confirm.ask("No projects found. Create new project?"):
                    name = Prompt.ask("Project name")
                    description = Prompt.ask("Description", default="")
                    repo_url = Prompt.ask("Repository URL", default="")
                    
                    project = client.create_project(workspace_id, name, description, repo_url)
                    project_id = project["id"]
                    console.print(f"[green]✓[/green] Created project: {name}")
                else:
                    raise click.Abort()
            else:
                table = Table(title="Available Projects")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description")
                
                for proj in projects:
                    table.add_row(str(proj["id"]), proj["project_name"], proj.get("details", ""))
                
                console.print(table)
                project_id = int(Prompt.ask("Select project ID"))
        
        # Save project config
        config.save_project_config({
            "workspace_id": workspace_id,
            "project_id": project_id
        })
        
        project = client.get_project(project_id)
        
        console.print(Panel.fit(
            f"[green]✓[/green] Initialized Nexula project\n\n"
            f"Workspace ID: [bold]{workspace_id}[/bold]\n"
            f"Project: [bold]{project['project_name']}[/bold] (ID: {project_id})\n\n"
            f"Next steps:\n"
            f"  1. Generate AIBOM: [bold]nexula aibom generate[/bold]\n"
            f"  2. Run security scan: [bold]nexula scan run[/bold]",
            title="[green]Project Initialized[/green]",
            border_style="green"
        ))
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()
