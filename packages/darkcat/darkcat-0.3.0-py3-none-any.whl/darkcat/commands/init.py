# darkcat/commands/init.py
import click
import os
import shutil

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "templates")

def create_project(template_type, template_name, project_name, folder=None):
    """Core logic to create a project, can be called by wizard"""
    if folder is None:
        folder = os.getcwd()
    dest_path = os.path.join(folder, project_name)
    src_path = os.path.join(TEMPLATES_PATH, template_type, template_name)

    if not os.path.exists(src_path):
        click.secho(f"❌ Template '{template_name}' not found for {template_type}", fg="red")
        return

    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

    # Replace placeholders
    for root, _, files in os.walk(dest_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                content = f.read()
            content = content.replace("{{ project_name }}", project_name)
            with open(file_path, "w") as f:
                f.write(content)

    click.secho(f"🌐 Project '{project_name}' created using '{template_name}' template!", fg="green")


@click.group()
def init():
    """Initialize new projects"""
    pass

@init.command()
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--template", type=click.Choice(["default","minimal"]), default="default")
def web(name, template):
    create_project("web", template, name)

@init.command()
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--template", type=click.Choice(["default","minimal"]), default="default")
def api(name, template):
    create_project("api", template, name)
