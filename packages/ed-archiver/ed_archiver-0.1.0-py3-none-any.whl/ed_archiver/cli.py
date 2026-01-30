"""Command-line interface for ed-archiver."""

import sys
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.prompt import Prompt

from ed_archiver.archiver import Archiver
from ed_archiver.client import create_client
from ed_archiver.parser import parse_input

console = Console()


def main() -> None:
    """Entry point for ed-archiver CLI."""
    console.print(
        "[bold magenta]Ed Archiver[/] - Export Ed discussions to RAG-ready JSON\n"
    )

    args = sys.argv[1:]
    output_dir = _parse_output_dir(args)

    # Get course input (ID or URL)
    raw_input = _parse_course_input(args)
    if not raw_input:
        raw_input = Prompt.ask(
            "Enter course ID or URL",
            console=console,
        )

    # Parse input to extract course ID and region
    try:
        ed_url = parse_input(raw_input)
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise SystemExit(1)

    console.print(
        f"Course: [cyan]{ed_url.course_id}[/] | Region: [cyan]{ed_url.region}[/]\n"
    )

    # Create region-aware client and authenticate
    client = create_client(ed_url.region)

    try:
        client.login()
    except Exception as e:
        console.print(f"[red]Authentication failed:[/] {e}")
        raise SystemExit(1)

    console.print()

    # Archive the course
    archiver = Archiver(ed_client=client, region=ed_url.region, output_dir=output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        try:
            course_dir = archiver.archive_course(ed_url.course_id, progress=progress)
        except ValueError as e:
            console.print(f"[red]Error:[/] {e}")
            raise SystemExit(1)

    console.print(f"\n[green]Done![/] Archived to [bold]{course_dir}[/]")


def _parse_course_input(args: list[str]) -> str | None:
    """Extract course ID or URL from positional args.

    Args:
        args: Command line arguments.

    Returns:
        Course ID/URL string or None if not provided.
    """
    for arg in args:
        if not arg.startswith("-"):
            return arg
    return None


def _parse_output_dir(args: list[str]) -> Path:
    """Extract output directory from -o flag.

    Args:
        args: Command line arguments.

    Returns:
        Output directory path (defaults to "out").
    """
    for i, arg in enumerate(args):
        if arg in ("-o", "--output") and i + 1 < len(args):
            return Path(args[i + 1])
    return Path("out")


if __name__ == "__main__":
    main()
