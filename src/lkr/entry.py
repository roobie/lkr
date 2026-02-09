"""Entry CRUD operations — parsing boundary."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import frontmatter

from lkr.errors import EntryParseError
from lkr.idgen import generate_id
from lkr.models import Entry, EntryFrontMatter, EntryType, Tag
from lkr.templates import get_template


def parse_entry(path: Path) -> Entry:
    """Parse a markdown file into a fully typed Entry.

    This is THE parsing boundary: raw YAML + markdown is converted into
    typed domain objects. If anything is invalid, EntryParseError is raised.
    No downstream code ever re-validates.
    """
    try:
        post = frontmatter.load(str(path))
    except Exception as e:
        raise EntryParseError(str(path), f"Failed to read: {e}") from e

    try:
        fm = EntryFrontMatter(**post.metadata)
    except Exception as e:
        raise EntryParseError(str(path), f"Invalid front matter: {e}") from e

    return Entry(front_matter=fm, body=post.content, source_path=path)


def serialize_entry(entry: Entry) -> str:
    """Convert an Entry back to markdown with YAML front matter."""
    fm = entry.front_matter
    metadata: dict = {
        "id": fm.id.value,
        "title": fm.title,
        "type": fm.type.value,
        "tags": [t.value for t in fm.tags],
        "created": fm.created.isoformat(),
    }
    if fm.updated is not None:
        metadata["updated"] = fm.updated.isoformat()
    if fm.status is not None:
        metadata["status"] = fm.status.value
    if fm.difficulty is not None:
        metadata["difficulty"] = fm.difficulty
    if fm.author is not None:
        metadata["author"] = fm.author
    if fm.related:
        metadata["related"] = [r.value for r in fm.related]
    if fm.source is not None:
        metadata["source"] = fm.source

    post = frontmatter.Post(entry.body, **metadata)
    return frontmatter.dumps(post) + "\n"


def write_entry(entry: Entry, path: Path) -> None:
    """Write a serialized entry to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_entry(entry))


def create_entry(
    entry_type: EntryType,
    title: str,
    tags: list[str],
    author: str | None = None,
) -> Entry:
    """Create a new Entry with a generated ID and body template."""
    entry_id = generate_id()
    parsed_tags = [Tag(t) for t in tags]
    body = get_template(entry_type)

    fm = EntryFrontMatter(
        id=entry_id,
        title=title,
        type=entry_type,
        tags=parsed_tags,
        created=date.today(),
        status="draft",
        author=author,
    )

    return Entry(front_matter=fm, body=body)
