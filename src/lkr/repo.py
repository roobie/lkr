"""Repository discovery and operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

import yaml

from lkr.entry import parse_entry, write_entry
from lkr.errors import EntryNotFoundError, EntryParseError, RepoNotFoundError
from lkr.models import Entry, EntryId, RepoConfig

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = """\
version: "0.1.0"
name: "{name}"
description: ""
"""

_DEFAULT_README = """\
# {name}

A knowledge repository managed by [lkr](https://github.com/lkr).
"""

_GITIGNORE_ADDITIONS = """\
# LKR
.knowledge/index.json
"""


class KnowledgeRepo:
    """Represents a knowledge repository on disk."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.entries_dir = root / "entries"
        self.knowledge_dir = root / ".knowledge"

    @classmethod
    def discover(cls, start: Path | None = None) -> "KnowledgeRepo":
        """Walk up from start (default: cwd) looking for .knowledge/config.yaml."""
        current = (start or Path.cwd()).resolve()
        while True:
            if (current / ".knowledge" / "config.yaml").is_file():
                return cls(current)
            parent = current.parent
            if parent == current:
                break
            current = parent
        raise RepoNotFoundError(
            "No knowledge repository found. Run 'k init' to create one."
        )

    @classmethod
    def init(cls, path: Path, name: str) -> "KnowledgeRepo":
        """Initialize a new knowledge repository."""
        root = path.resolve()
        entries_dir = root / "entries"
        knowledge_dir = root / ".knowledge"

        entries_dir.mkdir(parents=True, exist_ok=True)
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        config_path = knowledge_dir / "config.yaml"
        if not config_path.exists():
            config_path.write_text(_DEFAULT_CONFIG.format(name=name))

        readme_path = root / "README.md"
        if not readme_path.exists():
            readme_path.write_text(_DEFAULT_README.format(name=name))

        gitignore_path = root / ".gitignore"
        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            if ".knowledge/index.json" not in existing:
                gitignore_path.write_text(existing.rstrip() + "\n" + _GITIGNORE_ADDITIONS)
        else:
            gitignore_path.write_text(_GITIGNORE_ADDITIONS)

        return cls(root)

    def load_config(self) -> RepoConfig:
        """Parse .knowledge/config.yaml into RepoConfig."""
        config_path = self.knowledge_dir / "config.yaml"
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return RepoConfig(**data)

    def entry_path(self, entry_id: EntryId) -> Path:
        """Compute path for an entry: entries/{prefix}/{id}.md."""
        return self.entries_dir / entry_id.prefix / f"{entry_id.value}.md"

    def iter_entries(self) -> Iterator[Entry]:
        """Parse all .md files under entries/, yielding Entry objects."""
        if not self.entries_dir.exists():
            return
        for md_file in sorted(self.entries_dir.rglob("*.md")):
            try:
                yield parse_entry(md_file)
            except EntryParseError as e:
                logger.warning("Skipping %s: %s", md_file, e)

    def resolve_entry(self, raw_id: str) -> Entry:
        """Parse raw string to EntryId, locate file, parse to Entry."""
        try:
            entry_id = EntryId(raw_id)
        except ValueError as e:
            raise EntryNotFoundError(raw_id) from e

        path = self.entry_path(entry_id)
        if not path.is_file():
            raise EntryNotFoundError(raw_id)

        return parse_entry(path)

    def save_entry(self, entry: Entry) -> Path:
        """Save an entry to its correct location and return the path."""
        path = self.entry_path(entry.front_matter.id)
        write_entry(entry, path)
        return path
