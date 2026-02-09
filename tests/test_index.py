"""Tests for index generation."""

import json

from lkr.index import build_index, write_index
from lkr.repo import KnowledgeRepo


def test_build_index_empty(tmp_repo: KnowledgeRepo):
    index = build_index(tmp_repo)
    assert index.entry_count == 0
    assert index.entries == []


def test_build_index_populated(populated_repo: KnowledgeRepo):
    index = build_index(populated_repo)
    assert index.entry_count == 3
    assert len(index.entries) == 3

    # Check tag index
    assert "python" in index.tag_index
    assert len(index.tag_index["python"]) == 2  # q-and-a + note

    # Check type index
    assert "q-and-a" in index.type_index
    assert "guide" in index.type_index
    assert "note" in index.type_index


def test_write_index(populated_repo: KnowledgeRepo):
    index = write_index(populated_repo)
    index_path = populated_repo.knowledge_dir / "index.json"
    assert index_path.exists()

    data = json.loads(index_path.read_text())
    assert data["entry_count"] == 3
    assert "generated" in data
    assert len(data["entries"]) == 3
