"""CLI for parsing and analyzing Vector CANoe XML test reports."""

__author__ = "Mohamed Hamed Othman"
__email__ = "mohamedahamed1915@gmail.com"

import typer
from typing import List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .parser import CanoeReportParser
from .formatters import SummaryFormatter, FailureFormatter, DetailedFormatter

app = typer.Typer(help="Vector CANoe XML Test Report Parser CLI")
console = Console()
err_console = Console(stderr=True)


def resolve_files(paths: List[Path]) -> List[Path]:
    """Expands directories into a list of XML files."""
    resolved = []
    for p in paths:
        if p.is_file():
            if p.suffix.lower() == ".xml":
                resolved.append(p)
            else:
                err_console.print(
                    f"[yellow]Warning:[/yellow] Skipping non-XML file {p}"
                )
        elif p.is_dir():
            xml_files = list(p.glob("*.xml"))
            if not xml_files:
                err_console.print(
                    f"[yellow]Warning:[/yellow] No XML files found in directory {p}"
                )
            resolved.extend(xml_files)
        else:
            err_console.print(f"[bold red]Error:[/bold red] Path {p} does not exist.")
    return resolved


@app.command()
def summary(
    files: List[Path] = typer.Argument(
        ..., help="Path to one or more CANoe XML reports or directories."
    ),
    exit_on_error: bool = typer.Option(
        False, "--exit-on-error", "-e", help="Exit immediately on first error."
    ),
):
    """
    Get a high-level summary of test results from one or more reports.
    """
    target_files = resolve_files(files)
    if not target_files:
        raise typer.Exit(code=1)

    has_errors = False
    for file in target_files:
        try:
            with console.status(f"[bold green]Parsing {file.name}..."):
                parser = CanoeReportParser(str(file))
                report = parser.parse()
            SummaryFormatter.print_summary(report)
        except Exception as e:
            err_console.print(f"[bold red]Error processing {file.name}:[/bold red] {e}")
            has_errors = True
            if exit_on_error:
                raise typer.Exit(code=1)

    if has_errors:
        raise typer.Exit(code=1)


@app.command()
def failures(
    files: List[Path] = typer.Argument(
        ..., help="Path to one or more CANoe XML reports or directories."
    ),
    exit_on_error: bool = typer.Option(
        False, "--exit-on-error", "-e", help="Exit immediately on first error."
    ),
):
    """
    Show detailed failure information, including context logs and diagnostic data.
    """
    target_files = resolve_files(files)
    if not target_files:
        raise typer.Exit(code=1)

    has_errors = False
    for file in target_files:
        try:
            parser = CanoeReportParser(str(file))
            report = parser.parse()
            FailureFormatter.print_failures(report)
        except Exception as e:
            err_console.print(f"[bold red]Error processing {file.name}:[/bold red] {e}")
            has_errors = True
            if exit_on_error:
                raise typer.Exit(code=1)

    if has_errors:
        raise typer.Exit(code=1)


@app.command()
def inspect(
    files: List[Path] = typer.Argument(
        ..., help="Path to one or more CANoe XML reports or directories."
    ),
    test_case: str = typer.Option(
        ...,
        "--test-case",
        "-t",
        help="Search term for test case title (case-insensitive).",
    ),
    exit_on_error: bool = typer.Option(
        False, "--exit-on-error", "-e", help="Exit immediately on first error."
    ),
):
    """
    Inspect full logs for specific test cases matching a search term.
    """
    target_files = resolve_files(files)
    if not target_files:
        raise typer.Exit(code=1)

    has_errors = False
    for file in target_files:
        try:
            parser = CanoeReportParser(str(file))
            report = parser.parse()

            # Gather all test cases
            all_cases = []
            for group in report.root_groups:
                all_cases.extend(group.get_all_test_cases())

            search_term = test_case.lower()
            found_cases = [tc for tc in all_cases if search_term in tc.title.lower()]

            if not found_cases:
                console.print(
                    f"[yellow]![/yellow] No test cases matching '[bold]{test_case}[/bold]' in {file.name}"
                )
                continue

            console.print(Panel(f"Matches in {file.name}", style="blue"))
            DetailedFormatter.print_test_case(report.name, found_cases)

        except Exception as e:
            err_console.print(f"[bold red]Error processing {file.name}:[/bold red] {e}")
            has_errors = True
            if exit_on_error:
                raise typer.Exit(code=1)

    if has_errors:
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    CANoe Report Parser - A powerful CLI to analyze Vector CANoe XML reports.
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
