"""CLI interface for mdstruct."""

import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from mdstruct import __version__
from mdstruct.core import join_markdown, split_markdown

app = typer.Typer(
    name="mdstruct",
    help="Split and recombine markdown files by ATX headers",
    add_completion=False,
)
console = Console()


def _do_split(input_path: Path, output_dir: Path, level: int | None, force: bool) -> None:
    """Internal helper to perform split operation with cleanup."""
    # Check if output directory exists and confirm overwrite
    if output_dir.exists() and not force:
        if not typer.confirm(
            f"⚠️  {output_dir}/ already exists. Overwrite?",
            default=False,
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        console.print(f"[cyan]Splitting[/cyan] {input_path} → {output_dir}/")
        split_markdown(input_path, output_dir, level=level)

        # Move the original markdown file to /tmp/mdstruct/ after successful split
        tmp_dir = Path("/tmp/mdstruct")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / input_path.name
        if tmp_path.exists():
            tmp_path.unlink()
        shutil.move(str(input_path), str(tmp_path))
        console.print(f"[dim]Moved original file to: {tmp_path}[/dim]")

        console.print(Panel(f"✓ Split complete: {output_dir}/", style="green"))
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def _do_join(input_dir: Path, output_path: Path, force: bool) -> None:
    """Internal helper to perform join operation with cleanup."""
    # Check if output file exists and confirm overwrite
    if output_path.exists() and not force:
        if not typer.confirm(
            f"⚠️  {output_path} already exists. Overwrite?",
            default=False,
        ):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        console.print(f"[cyan]Joining[/cyan] {input_dir}/ → {output_path}")
        join_markdown(input_dir, output_path)

        # Move the original directory to /tmp/mdstruct/ after successful join
        tmp_dir = Path("/tmp/mdstruct")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / input_dir.name
        if tmp_path.exists():
            shutil.rmtree(tmp_path)
        shutil.move(str(input_dir), str(tmp_path))
        console.print(f"[dim]Moved original folder to: {tmp_path}/[/dim]")

        console.print(Panel(f"✓ Join complete: {output_path}", style="green"))
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"mdstruct version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Markdown structure manipulation.

    Auto-detects whether to split or join based on path:
    - If path.md exists: split it
    - If path/ directory exists: join it
    - If both exist: error (requires explicit split/join command)

    Examples:
        mdstruct foo          # auto-detects based on foo.md or foo/
        mdstruct foo.md       # splits foo.md into foo/
        mdstruct foo/         # joins foo/ into foo.md
        mdstruct split foo    # explicit split
        mdstruct join foo     # explicit join
    """
    pass


@app.command()
def split(
    path: str = typer.Argument(..., help="Path to markdown file (e.g., 'foo' or 'foo.md')"),
    level: int | None = typer.Option(
        None,
        "--level",
        "-l",
        help="Maximum heading level to split at (default: auto-detect based on content)",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output directory (default: inferred from input)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing output without confirmation"
    ),
):
    """
    Split a markdown file hierarchically by headers.

    Splits at H1, then at H2s within each H1, up to the specified level.

    Examples:
        mdstruct split foo          # splits foo.md into foo/
        mdstruct split foo.md       # splits foo.md into foo/
        mdstruct split foo -l 3     # split up to H3 level
    """
    # Smart path handling
    input_path = Path(path)
    if not input_path.suffix:
        input_path = input_path.with_suffix(".md")

    # Infer output directory
    if output:
        output_dir = Path(output)
    else:
        output_dir = input_path.with_suffix("")

    _do_split(input_path, output_dir, level, force)


@app.command()
def join(
    path: str = typer.Argument(..., help="Path to directory (e.g., 'foo' or 'foo/')"),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file (default: inferred from input)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing output without confirmation"
    ),
):
    """
    Join split markdown files back into a single file.

    Examples:
        mdstruct join foo           # joins foo/ into foo.md
        mdstruct join foo/          # joins foo/ into foo.md
        mdstruct join foo -o out.md # joins foo/ into out.md
    """
    # Smart path handling
    input_dir = Path(path)
    if input_dir.suffix == ".md":
        input_dir = input_dir.with_suffix("")

    # Infer output file
    if output:
        output_path = Path(output)
    else:
        output_path = input_dir.with_suffix(".md")

    _do_join(input_dir, output_path, force)


@app.command()
def auto(
    path: str = typer.Argument(..., help="Path to file or directory"),
    level: int | None = typer.Option(
        None,
        "--level",
        "-l",
        help="Maximum heading level to split at (for split operation)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file/directory",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing output without confirmation"
    ),
):
    """
    Auto-detect whether to split or join based on path.

    Checks what exists:
    - If path.md exists: split it
    - If path/ directory exists: join it
    - If both exist: error (requires explicit split/join command)

    Examples:
        mdstruct foo         # same as: mdstruct auto foo
        mdstruct auto foo    # explicit auto command
    """
    base_path = Path(path)
    md_file = base_path.with_suffix(".md") if not base_path.suffix else base_path
    dir_path = base_path.with_suffix("") if base_path.suffix == ".md" else base_path

    md_exists = md_file.exists() and md_file.is_file()
    dir_exists = dir_path.exists() and dir_path.is_dir()

    if md_exists and dir_exists:
        console.print(
            f"[red]Error:[/red] Both {md_file} and {dir_path}/ exist.\n"
            "Please be explicit: use 'mdstruct split' or 'mdstruct join'"
        )
        raise typer.Exit(1)
    elif md_exists:
        # Auto-detect: split
        console.print(f"[dim]Auto-detected: splitting {md_file}[/dim]")
        output_dir = Path(output) if output else md_file.with_suffix("")
        _do_split(md_file, output_dir, level, force)
    elif dir_exists:
        # Auto-detect: join
        console.print(f"[dim]Auto-detected: joining {dir_path}/[/dim]")
        output_file = Path(output) if output else dir_path.with_suffix(".md")
        _do_join(dir_path, output_file, force)
    else:
        console.print(
            f"[red]Error:[/red] Neither {md_file} nor {dir_path}/ exists.\n"
            f"Create one of them first or use explicit split/join commands."
        )
        raise typer.Exit(1)


def cli():
    """Main CLI entry point with auto-command injection."""
    # Auto-inject 'auto' command if first arg is not a known command
    from typer.main import get_command

    # Get list of known command names
    command_obj = get_command(app)
    known_commands = list(command_obj.commands.keys()) if hasattr(command_obj, "commands") else []

    # If there are args and first arg is not a known command, insert 'auto'
    if len(sys.argv) > 1 and sys.argv[1] not in known_commands and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "auto")

    app()


if __name__ == "__main__":
    cli()
