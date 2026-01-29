"""Console output utilities using Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Global console instance
console = Console()
error_console = Console(stderr=True)


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Message to print.
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Message to print.
    """
    error_console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Message to print.
    """
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: Message to print.
    """
    console.print(f"[blue]i[/blue] {message}")


def print_module_list(
    modules: list[tuple[str, str, bool]],
    title: str = "Available Modules",
    show_numbers: bool = True,
) -> None:
    """Print a table of modules.

    Args:
        modules: List of (name, source, enabled) tuples.
        title: Table title.
        show_numbers: Whether to show row numbers for selection.
    """
    table = Table(title=title)
    if show_numbers:
        table.add_column("#", style="dim", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Source", style="dim")
    table.add_column("Status", justify="center")

    for idx, (name, source, enabled) in enumerate(modules, start=1):
        status = "[green]●[/green]" if enabled else "[dim]○[/dim]"
        if show_numbers:
            table.add_row(str(idx), name, source, status)
        else:
            table.add_row(name, source, status)

    console.print(table)


def print_diff(old_content: str | None, new_content: str | None, name: str) -> None:
    """Print a diff between old and new content.

    Args:
        old_content: Original content (None for additions).
        new_content: New content (None for deletions).
        name: Name of the item being diffed.
    """
    if old_content is None and new_content is not None:
        console.print(
            Panel(
                f"[green]+ New module: {name}[/green]",
                title="Addition",
                border_style="green",
            )
        )
    elif old_content is not None and new_content is None:
        console.print(
            Panel(
                f"[red]- Removed module: {name}[/red]",
                title="Removal",
                border_style="red",
            )
        )
    elif old_content != new_content:
        console.print(
            Panel(
                f"[yellow]~ Modified module: {name}[/yellow]",
                title="Modification",
                border_style="yellow",
            )
        )
    else:
        console.print(f"[dim]No changes to {name}[/dim]")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for user confirmation.

    Args:
        message: Confirmation message.
        default: Default value if user just presses Enter.

    Returns:
        True if confirmed, False otherwise.
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = console.input(f"{message}{suffix}: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")


def print_command_header(command: str, description: str) -> None:
    """Print a header for a command.

    Args:
        command: Command name.
        description: Command description.
    """
    text = Text()
    text.append(f"dd-dm {command}", style="bold cyan")
    text.append(f" - {description}", style="dim")
    console.print(text)
    console.print()
