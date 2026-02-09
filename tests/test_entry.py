"""Tests for entry parsing and serialization."""

from pathlib import Path

import pytest

from lkr.entry import create_entry, parse_entry, serialize_entry, write_entry
from lkr.errors import EntryParseError
from lkr.models import EntryType


def test_parse_entry(tmp_path: Path, sample_entry_text: str):
    path = tmp_path / "ab" / "ab123456.md"
    path.parent.mkdir(parents=True)
    path.write_text(sample_entry_text)

    entry = parse_entry(path)
    assert entry.front_matter.id.value == "ab123456"
    assert entry.front_matter.title == "Test Entry"
    assert entry.front_matter.type == EntryType.Q_AND_A
    assert len(entry.front_matter.tags) == 2
    assert "pytest" in entry.body


def test_parse_entry_invalid_yaml(tmp_path: Path):
    path = tmp_path / "bad.md"
    path.write_text("---\n: invalid yaml: [\n---\nbody\n")

    with pytest.raises(EntryParseError):
        parse_entry(path)


def test_parse_entry_missing_fields(tmp_path: Path):
    path = tmp_path / "missing.md"
    path.write_text("---\ntitle: Only Title\n---\nbody\n")

    with pytest.raises(EntryParseError):
        parse_entry(path)


def test_serialize_roundtrip(tmp_path: Path, sample_entry_text: str):
    path = tmp_path / "ab" / "ab123456.md"
    path.parent.mkdir(parents=True)
    path.write_text(sample_entry_text)

    entry = parse_entry(path)
    text = serialize_entry(entry)

    # Write and re-parse
    path2 = tmp_path / "ab" / "roundtrip.md"
    path2.write_text(text)
    entry2 = parse_entry(path2)

    assert entry2.front_matter.id == entry.front_matter.id
    assert entry2.front_matter.title == entry.front_matter.title
    assert entry2.front_matter.type == entry.front_matter.type
    assert len(entry2.front_matter.tags) == len(entry.front_matter.tags)


def test_create_entry():
    entry = create_entry(
        entry_type=EntryType.Q_AND_A,
        title="How to test",
        tags=["python", "testing"],
        author="alice",
    )
    assert len(entry.front_matter.id.value) == 8
    assert entry.front_matter.title == "How to test"
    assert entry.front_matter.type == EntryType.Q_AND_A
    assert entry.front_matter.author == "alice"
    assert "## Question" in entry.body


def test_create_entry_guide():
    entry = create_entry(EntryType.GUIDE, "Setup Guide", ["devops"])
    assert "## Steps" in entry.body


def test_create_entry_pattern():
    entry = create_entry(EntryType.PATTERN, "Singleton", ["design"])
    assert "## Solution" in entry.body


def test_create_entry_note():
    entry = create_entry(EntryType.NOTE, "Quick Note", ["misc"])
    assert "## Summary" in entry.body


def test_write_entry(tmp_path: Path):
    entry = create_entry(EntryType.NOTE, "Write Test", ["test"])
    path = tmp_path / entry.front_matter.id.prefix / f"{entry.front_matter.id.value}.md"
    write_entry(entry, path)

    assert path.exists()
    reparsed = parse_entry(path)
    assert reparsed.front_matter.id == entry.front_matter.id
