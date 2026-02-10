"""Repository validation — reporting tool, not gatekeeper."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
import re

from lkr.entry import parse_entry
from lkr.errors import EntryParseError
from lkr.models import Entry

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lkr.repo import KnowledgeRepo


@dataclass
class ValidationIssue:
    level: str  # "error" or "warning"
    file: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)
    entries_checked: int = 0
    errors: int = 0
    warnings: int = 0

    @property
    def is_clean(self) -> bool:
        return self.errors == 0 and self.warnings == 0

    def add_error(self, file: str, message: str) -> None:
        self.issues.append(ValidationIssue("error", file, message))
        self.errors += 1

    def add_warning(self, file: str, message: str) -> None:
        self.issues.append(ValidationIssue("warning", file, message))
        self.warnings += 1


def validate_repo(repo: "KnowledgeRepo") -> ValidationReport:
    """Run all validation checks and return a report."""
    report = ValidationReport()
    entries: list[Entry] = []
    entry_files = (
        sorted(repo.entries_dir.rglob("*.md")) if repo.entries_dir.exists() else []
    )

    # 1. Schema compliance — try to parse each entry
    for md_file in entry_files:
        report.entries_checked += 1
        try:
            entry = parse_entry(md_file)
            entries.append(entry)
        except EntryParseError as e:
            report.add_error(str(md_file.relative_to(repo.root)), e.reason)
            continue

        fm = entry.front_matter
        rel_path = str(md_file.relative_to(repo.root))

        # 4. File naming — filename matches ID and title slug
        words = re.sub(r'[^a-zA-Z0-9\s]', '', fm.title).split()
        words = words[:8]
        slug = '-'.join(w.lower() for w in words if w)
        expected_filename = f"{fm.id.value}-{slug}.md" if slug else f"{fm.id.value}.md"
        if md_file.name != expected_filename:
            report.add_error(
                rel_path,
                f"Filename {md_file.name!r} doesn't match ID {fm.id.value!r} and title slug",
            )

        # 5. Directory structure — parent dir matches ID prefix
        parent_name = md_file.parent.name
        if parent_name != fm.id.prefix:
            report.add_error(
                rel_path,
                f"Directory {parent_name!r} doesn't match ID prefix {fm.id.prefix!r}",
            )

    # 2. Uniqueness — duplicate IDs
    seen_ids: dict[str, str] = {}
    for entry in entries:
        id_str = entry.front_matter.id.value
        rel = (
            str(entry.source_path.relative_to(repo.root))
            if entry.source_path
            else id_str
        )
        if id_str in seen_ids:
            report.add_error(
                rel, f"Duplicate ID {id_str!r} (also in {seen_ids[id_str]})"
            )
        else:
            seen_ids[id_str] = rel

    # 3. References — related IDs exist
    for entry in entries:
        if entry.front_matter.related:
            rel = (
                str(entry.source_path.relative_to(repo.root))
                if entry.source_path
                else ""
            )
            for ref in entry.front_matter.related:
                if ref.value not in seen_ids:
                    report.add_error(rel, f"Related ID {ref.value!r} not found")

    # 6. Warnings — old drafts, stale entries
    today = date.today()
    for entry in entries:
        fm = entry.front_matter
        rel = str(entry.source_path.relative_to(repo.root)) if entry.source_path else ""

        if fm.status and fm.status.value == "draft":
            age = (today - fm.created).days
            if age > 30:
                report.add_warning(rel, f"Draft entry is {age} days old")

        if fm.updated is None:
            age = (today - fm.created).days
            if age > 180:
                report.add_warning(
                    rel, f"Entry has no 'updated' date and is {age} days old"
                )

    return report
