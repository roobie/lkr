"""CLI entry point — Click commands."""

from __future__ import annotations

import functools
from pathlib import Path

import click

from lkr.console import (
    console,
    print_entry_summary,
    print_error,
    print_search_results,
    print_success,
    print_validation_report,
)
from lkr.errors import KnowledgeError


def handle_errors(f):
    """Decorator to catch KnowledgeError and print user-friendly messages."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KnowledgeError as e:
            print_error(str(e))
            raise SystemExit(1) from e

    return wrapper


@click.group()
def cli():
    """LKR — Knowledge Repository Manager."""


@cli.command()
@click.argument("name")
@handle_errors
def init(name: str):
    """Initialize a new knowledge repository."""
    from lkr.repo import KnowledgeRepo

    repo = KnowledgeRepo.init(Path.cwd(), name)
    print_success(f"Initialized knowledge repository '{name}' at {repo.root}")


@cli.command()
@click.argument(
    "entry_type",
    type=click.Choice(["q-and-a", "guide", "pattern", "note"]),
)
@click.argument("title")
@click.option("-t", "--tag", multiple=True, help="Tags for the entry.")
@click.option("-a", "--author", default=None, help="Author name.")
@handle_errors
def new(entry_type: str, title: str, tag: tuple[str, ...], author: str | None):
    """Create a new entry."""
    from lkr.entry import create_entry
    from lkr.models import EntryType
    from lkr.repo import KnowledgeRepo

    repo = KnowledgeRepo.discover()
    entry = create_entry(
        entry_type=EntryType(entry_type),
        title=title,
        tags=list(tag),
        author=author,
    )
    path = repo.save_entry(entry)
    print_success(f"Created {entry.front_matter.id} at {path}")


@cli.command()
@click.argument("query")
@click.option("-t", "--tag", default=None, help="Filter by tag.")
@click.option("--type", "entry_type", default=None, help="Filter by entry type.")
@handle_errors
def search(query: str, tag: str | None, entry_type: str | None):
    """Search entries."""
    from lkr.repo import KnowledgeRepo
    from lkr.search import search as do_search

    repo = KnowledgeRepo.discover()
    results = do_search(query, repo.entries_dir, tag=tag, entry_type=entry_type)
    print_search_results(results)


@cli.command()
@click.argument("entry_id")
@handle_errors
def get(entry_id: str):
    """Show entry summary."""
    from lkr.repo import KnowledgeRepo

    repo = KnowledgeRepo.discover()
    entry = repo.resolve_entry(entry_id)
    print_entry_summary(entry)


@cli.command()
@click.argument("entry_id")
@handle_errors
def cat(entry_id: str):
    """Print raw entry to stdout."""
    from lkr.repo import KnowledgeRepo

    repo = KnowledgeRepo.discover()
    entry = repo.resolve_entry(entry_id)
    if entry.source_path:
        click.echo(entry.source_path.read_text(), nl=False)


@cli.command()
@handle_errors
def validate():
    """Validate all entries."""
    from lkr.repo import KnowledgeRepo
    from lkr.validate import validate_repo

    repo = KnowledgeRepo.discover()
    report = validate_repo(repo)
    print_validation_report(report)
    if report.errors:
        raise SystemExit(1)


@cli.command()
@handle_errors
def index():
    """Generate .knowledge/index.json."""
    from lkr.index import write_index
    from lkr.repo import KnowledgeRepo

    repo = KnowledgeRepo.discover()
    idx = write_index(repo)
    print_success(f"Index generated: {idx.entry_count} entries")
