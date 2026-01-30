import click
import shutil
from rich.console import Console
from rich.table import Table

console = Console()

AVAILABLE_TOOLS = ["git", "docker", "python", "node", "pip"]

@click.command()
def doctor():
    """Interactive system check for required tools"""
    console.print("🩺 [bold cyan]DarkCat Doctor[/bold cyan] running...\n")

    # Ask which tools to check
    choices = click.prompt(
        "Which tools do you want to check? (comma separated, or 'all')",
        default="all"
    )

    if choices.lower() == "all":
        tools_to_check = AVAILABLE_TOOLS
    else:
        tools_to_check = [tool.strip() for tool in choices.split(",")]

    # Prepare Rich table
    table = Table(title="System Check", show_header=True, header_style="bold magenta")
    table.add_column("Tool", justify="left")
    table.add_column("Status", justify="center")

    for tool in tools_to_check:
        if shutil.which(tool):
            table.add_row(tool, "[green]✅ Found[/green]")
        else:
            table.add_row(tool, "[red]❌ Missing[/red]")

    console.print(table)
    console.print("\n✔️ [bold green]System check complete![/bold green]")
