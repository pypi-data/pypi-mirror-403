import click
from rich.console import Console
from rich.panel import Panel
from ..config import config
from ..api_client import APIClient, APIError

console = Console()


@click.group()
def auth():
    """Authentication commands"""
    pass


@auth.command()
@click.option("--api-key", prompt="API Key", hide_input=True, help="Your Nexula API key")
@click.option("--api-url", default="http://localhost:8000/api/v1", help="API URL")
def login(api_key: str, api_url: str):
    """Login with API key"""
    try:
        # Save credentials
        config.set_api_key(api_key)
        config.set_api_url(api_url)
        
        # Verify authentication
        client = APIClient()
        user_info = client.verify_auth()
        
        console.print(Panel.fit(
            f"[green]✓[/green] Successfully authenticated as [bold]{user_info['organization_name']}[/bold]\n"
            f"Email: {user_info['email']}",
            title="[green]Login Successful[/green]",
            border_style="green"
        ))
        
    except APIError as e:
        config.clear()
        console.print(f"[red]✗[/red] Authentication failed: {e}", style="red")
        raise click.Abort()


@auth.command()
def logout():
    """Logout and clear credentials"""
    config.clear()
    console.print("[green]✓[/green] Logged out successfully")


@auth.command()
def whoami():
    """Show current authentication status"""
    try:
        client = APIClient()
        user_info = client.verify_auth()
        
        console.print(Panel.fit(
            f"Organization: [bold]{user_info['organization_name']}[/bold]\n"
            f"Email: {user_info['email']}\n"
            f"API URL: {config.get_api_url()}",
            title="[blue]Current User[/blue]",
            border_style="blue"
        ))
        
    except APIError as e:
        console.print(f"[red]✗[/red] Not authenticated: {e}", style="red")
        console.print("\nRun [bold]nexula auth login[/bold] to authenticate")
        raise click.Abort()
