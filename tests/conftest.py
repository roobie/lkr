"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from lkr.repo import KnowledgeRepo


SAMPLE_ENTRY = """\
---
id: "ab123456"
title: "Test Entry"
type: q-and-a
tags:
  - python
  - testing
created: 2025-01-15
status: draft
---

## Question

How do I test?

## Answers

### Answer 1

Use pytest.
"""


@pytest.fixture
def tmp_repo(tmp_path: Path) -> KnowledgeRepo:
    """Initialize a knowledge repo in a temp directory."""
    return KnowledgeRepo.init(tmp_path, "Test KB")


@pytest.fixture
def sample_entry_text() -> str:
    """Return valid entry markdown string."""
    return SAMPLE_ENTRY


@pytest.fixture
def populated_repo(tmp_repo: KnowledgeRepo) -> KnowledgeRepo:
    """A repo with 3 diverse entries pre-created."""
    from lkr.entry import create_entry
    from lkr.models import EntryType

    entries = [
        create_entry(EntryType.Q_AND_A, "How to fix ImportError", ["python", "import"]),
        create_entry(
            EntryType.GUIDE, "Getting Started with Docker", ["docker", "devops"]
        ),
        create_entry(EntryType.NOTE, "Python GIL Notes", ["python", "concurrency"]),
    ]

    for entry in entries:
        tmp_repo.save_entry(entry)

    return tmp_repo
