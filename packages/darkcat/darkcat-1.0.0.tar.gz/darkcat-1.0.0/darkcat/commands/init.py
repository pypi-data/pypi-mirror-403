import click
import os
import shutil

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "templates")

def create_project(project_type, template_name, project_name, folder=None):
    """Core logic to copy template files and replace placeholders"""
    if folder is None:
        folder = os.getcwd()
    
    src_path = os.path.join(TEMPLATES_PATH, project_type, template_name)
    dest_path = os.path.join(folder, project_name)
    
    if not os.path.exists(src_path):
        click.secho(f"❌ Template '{template_name}' not found for {project_type}", fg="red")
        return

    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)

    # Replace {{ project_name }} in all files
    for root, _, files in os.walk(dest_path):
        for f in files:
            fp = os.path.join(root, f)
            with open(fp, "r") as file:
                content = file.read()
            content = content.replace("{{ project_name }}", project_name)
            with open(fp, "w") as file:
                file.write(content)

    click.secho(f"🌐 Project '{project_name}' created using '{template_name}' template!", fg="green")


@click.group()
def init():
    """Initialize new projects"""
    pass

@init.command()
@click.option("--name", prompt="Project name")
@click.option("--template", type=click.Choice(["default","minimal"]), default="default")
def web(name, template):
    create_project("web", template, name)

@init.command()
@click.option("--name", prompt="Project name")
@click.option("--template", type=click.Choice(["default","minimal"]), default="default")
def api(name, template):
    create_project("api", template, name)
