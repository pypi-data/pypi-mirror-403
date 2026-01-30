import click
from darkcat.version import __version__
from darkcat.commands.init import init
from darkcat.commands.add import add
from darkcat.commands.doctor import doctor
from darkcat.commands.wizard import wizard

@click.group()
@click.version_option(__version__, prog_name="DarkCat")
def cli():
    """🐈‍⬛ DarkCat — Developer Automation Tool"""
    pass

cli.add_command(init)
cli.add_command(add)
cli.add_command(doctor)
cli.add_command(wizard)

if __name__ == "__main__":
    cli()
