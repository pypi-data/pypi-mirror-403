import click

from darkcat.commands.init import init
from darkcat.commands.add import add
from darkcat.commands.doctor import doctor
from darkcat.commands.wizard import wizard
from darkcat.version import __version__


@click.group()
@click.version_option(
    version=__version__,
    prog_name="DarkCat",
    message="%(prog)s version %(version)s"
)
def cli():
    """🐈‍⬛ DarkCat — Developer Automation Tool"""
    pass


cli.add_command(init)
cli.add_command(add)
cli.add_command(doctor)
cli.add_command(wizard)


if __name__ == "__main__":
    cli()
