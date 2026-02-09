"""Tests for repo validation."""

from pathlib import Path

from lkr.entry import create_entry, serialize_entry
from lkr.models import EntryType
from lkr.repo import KnowledgeRepo
from lkr.validate import validate_repo


def test_validate_clean_repo(populated_repo: KnowledgeRepo):
    report = validate_repo(populated_repo)
    # May have warnings (drafts) but no errors
    assert report.errors == 0


def test_validate_empty_repo(tmp_repo: KnowledgeRepo):
    report = validate_repo(tmp_repo)
    assert report.is_clean
    assert report.entries_checked == 0


def test_validate_bad_schema(tmp_repo: KnowledgeRepo):
    bad_dir = tmp_repo.entries_dir / "xx"
    bad_dir.mkdir()
    (bad_dir / "xx000000.md").write_text("---\ntitle: Only Title\n---\nbody\n")

    report = validate_repo(tmp_repo)
    assert report.errors >= 1


def test_validate_duplicate_ids(tmp_repo: KnowledgeRepo):
    entry = create_entry(EntryType.NOTE, "First", ["test"])
    entry_id = entry.front_matter.id

    # Write same ID to two different files
    dir1 = tmp_repo.entries_dir / entry_id.prefix
    dir1.mkdir(parents=True, exist_ok=True)
    (dir1 / f"{entry_id.value}.md").write_text(serialize_entry(entry))

    # Create a copy with different filename but same front matter ID
    dir2 = tmp_repo.entries_dir / entry_id.prefix
    path2 = dir2 / f"{entry_id.value}_dup.md"
    path2.write_text(serialize_entry(entry))

    report = validate_repo(tmp_repo)
    # The dup file has wrong filename, and duplicate ID
    assert report.errors >= 1


def test_validate_wrong_filename(tmp_repo: KnowledgeRepo):
    entry = create_entry(EntryType.NOTE, "Misnamed", ["test"])
    entry_id = entry.front_matter.id

    # Write with wrong filename
    wrong_dir = tmp_repo.entries_dir / entry_id.prefix
    wrong_dir.mkdir(parents=True, exist_ok=True)
    (wrong_dir / "wrongname.md").write_text(serialize_entry(entry))

    report = validate_repo(tmp_repo)
    assert report.errors >= 1


def test_validate_wrong_directory(tmp_repo: KnowledgeRepo):
    entry = create_entry(EntryType.NOTE, "Wrong Dir", ["test"])
    entry_id = entry.front_matter.id

    # Write in wrong directory
    wrong_dir = tmp_repo.entries_dir / "zz"
    wrong_dir.mkdir(parents=True, exist_ok=True)
    (wrong_dir / f"{entry_id.value}.md").write_text(serialize_entry(entry))

    report = validate_repo(tmp_repo)
    assert report.errors >= 1


def test_validate_missing_related(tmp_repo: KnowledgeRepo):
    entry = create_entry(EntryType.NOTE, "With Ref", ["test"])
    # Manually set a related ID that doesn't exist
    text = serialize_entry(entry)
    text = text.replace("status: draft", "status: draft\nrelated:\n  - zzzzzzzz")

    entry_id = entry.front_matter.id
    d = tmp_repo.entries_dir / entry_id.prefix
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{entry_id.value}.md").write_text(text)

    report = validate_repo(tmp_repo)
    assert report.errors >= 1
