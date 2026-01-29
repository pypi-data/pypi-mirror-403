"""Main CLI application for dd-dm."""

import typer

from dd_dm import __version__
from dd_dm.commands import add, create, init, remove, update
from dd_dm.commands import list as list_cmd

app = typer.Typer(
    name="dd-dm",
    help="Dungeon Master - Manage shared engineering rules for projects",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"dd-dm version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Dungeon Master - Manage shared engineering rules for projects."""
    pass


# Register commands
app.command(name="init")(init.init_command)
app.command(name="list")(list_cmd.list_command)
app.command(name="add")(add.add_command)
app.command(name="remove")(remove.remove_command)
app.command(name="create")(create.create_command)
app.command(name="update")(update.update_command)


if __name__ == "__main__":
    app()
