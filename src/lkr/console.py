"""Rich console output helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from lkr.models import Entry
    from lkr.validate import ValidationReport
    from lkr.search import SearchResult

console = Console()


def print_success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}", style="red")


def print_warning(message: str) -> None:
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_entry_summary(entry: "Entry") -> None:
    fm = entry.front_matter
    console.print(f"[bold]{fm.title}[/bold]")
    console.print(f"  ID:      {fm.id}")
    console.print(f"  Type:    {fm.type}")
    console.print(f"  Tags:    {', '.join(str(t) for t in fm.tags)}")
    console.print(f"  Created: {fm.created}")
    if fm.status:
        console.print(f"  Status:  {fm.status}")
    if entry.source_path:
        console.print(f"  Path:    {entry.source_path}")


def print_validation_report(report: "ValidationReport") -> None:
    if report.is_clean:
        print_success(
            f"All {report.entries_checked} entries passed validation."
        )
        return

    table = Table(title="Validation Report")
    table.add_column("Level", style="bold")
    table.add_column("File")
    table.add_column("Message")

    for issue in report.issues:
        style = "red" if issue.level == "error" else "yellow"
        table.add_row(issue.level.upper(), issue.file, issue.message, style=style)

    console.print(table)
    console.print(
        f"\n{report.entries_checked} entries checked: "
        f"[red]{report.errors} errors[/red], "
        f"[yellow]{report.warnings} warnings[/yellow]"
    )


def print_search_results(results: list["SearchResult"]) -> None:
    if not results:
        print_warning("No results found.")
        return

    for r in results:
        console.print(f"[bold]{r.title}[/bold] ({r.entry_id})")
        console.print(f"  {r.path}")
        for line in r.matches[:3]:
            console.print(f"    {line.strip()}")
        console.print()
