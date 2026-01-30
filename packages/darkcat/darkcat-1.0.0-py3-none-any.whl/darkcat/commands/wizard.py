# darkcat/commands/wizard.py
import click
from darkcat.commands.init import create_project

@click.command()
def wizard():
    """Run interactive project setup wizard"""
    click.echo("🪄 Welcome to DarkCat Wizard Mode!\n")

    project_type = click.prompt(
        "Choose project type (web/api)",
        type=click.Choice(["web","api"]),
        default="web"
    )

    project_name = click.prompt("Enter project name", default="MyProject")
    template = click.prompt("Choose template (default/minimal)", type=click.Choice(["default","minimal"]), default="default")

    # Call the shared function
    create_project(project_type, template, project_name)

    if click.confirm("Do you want to add Docker support?"):
        from darkcat.commands.add import docker as add_docker
        add_docker()

    if click.confirm("Do you want to add environment template?"):
        from darkcat.commands.add import env as add_env
        add_env()

    click.echo("\n🎉 Project setup complete! You’re ready to code!")
