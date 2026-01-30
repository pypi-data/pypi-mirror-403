import click
import os

@click.group()
def add():
    """Add features to an existing project"""
    pass

@add.command()
def docker():
    """Add Docker support interactively"""
    # Ask for project folder
    project_folder = click.prompt("Enter your project folder", default=os.getcwd())
    project_folder = os.path.abspath(project_folder)

    # Ask for service name
    service_name = click.prompt("Service name", default="app")

    # Ask for exposed port
    port = click.prompt("Port to expose", default="8000")

    # Dockerfile content
    dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
"""

    # docker-compose content
    compose = f"""version: '3'
services:
  {service_name}:
    build: .
    ports:
      - "{port}:{port}"
"""

    with open(os.path.join(project_folder, "Dockerfile"), "w") as f:
        f.write(dockerfile)

    with open(os.path.join(project_folder, "docker-compose.yml"), "w") as f:
        f.write(compose)

    click.echo(f"🐳 Docker support added to {project_folder} (service: {service_name}, port: {port})")


@add.command()
def env():
    """Add environment template interactively"""
    project_folder = click.prompt("Enter your project folder", default=os.getcwd())
    project_folder = os.path.abspath(project_folder)

    env_name = click.prompt("Environment variable template name", default=".env.example")

    with open(os.path.join(project_folder, env_name), "w") as f:
        f.write("ENV=development\nDEBUG=True\n")

    click.echo(f"🔐 Environment template '{env_name}' created in {project_folder}")
