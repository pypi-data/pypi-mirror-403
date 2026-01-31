import click
from rich.console import Console
from .commands.auth import auth
from .commands.init import init
from .commands.aibom import aibom
from .commands.scan import scan

console = Console()

BANNER = """
[bold cyan]
╔╗╔┌─┐─┐ ┬┬ ┬┬  ┌─┐  ╔═╗╦  ╦
║║║├┤ ┌┴┬┘│ ││  ├─┤  ║  ║  ║
╝╚╝└─┘┴ └─└─┘┴─┘┴ ┴  ╚═╝╩═╝╩
[/bold cyan]
[dim]AI/ML Supply Chain Security Platform[/dim]
"""


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Nexula CLI - Enterprise AI/ML Supply Chain Security"""
    console.print(BANNER)


# Register commands
cli.add_command(auth)
cli.add_command(init)
cli.add_command(aibom)
cli.add_command(scan)


if __name__ == "__main__":
    cli()
