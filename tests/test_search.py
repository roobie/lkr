"""Tests for search."""

from lkr.repo import KnowledgeRepo
from lkr.search import search_python


def test_search_python_finds_match(populated_repo: KnowledgeRepo):
    results = search_python("Question", populated_repo.entries_dir)
    # The q-and-a entry has "## Question" in its template
    assert len(results) >= 1


def test_search_python_no_match(populated_repo: KnowledgeRepo):
    results = search_python("xyznonexistent", populated_repo.entries_dir)
    assert len(results) == 0


def test_search_python_case_insensitive(populated_repo: KnowledgeRepo):
    results_lower = search_python("question", populated_repo.entries_dir)
    results_upper = search_python("QUESTION", populated_repo.entries_dir)
    assert len(results_lower) == len(results_upper)


def test_search_python_empty_dir(tmp_repo: KnowledgeRepo):
    results = search_python("anything", tmp_repo.entries_dir)
    assert results == []
