"""Tests for domain models."""

import pytest

from lkr.models import (
    EntryFrontMatter,
    EntryId,
    EntryStatus,
    EntryType,
    Tag,
)


class TestEntryId:
    def test_valid(self):
        eid = EntryId("abc123")
        assert eid.value == "abc123"

    def test_normalizes_lowercase(self):
        eid = EntryId("ABC123")
        assert eid.value == "abc123"

    def test_prefix(self):
        eid = EntryId("fvb2iq3a")
        assert eid.prefix == "fv"

    def test_invalid_chars(self):
        with pytest.raises(ValueError):
            EntryId("abc-def")

    def test_too_long(self):
        with pytest.raises(ValueError):
            EntryId("123456789")

    def test_empty(self):
        with pytest.raises(ValueError):
            EntryId("")

    def test_equality(self):
        assert EntryId("abc") == EntryId("abc")
        assert EntryId("abc") != EntryId("def")

    def test_hashable(self):
        s = {EntryId("abc"), EntryId("abc"), EntryId("def")}
        assert len(s) == 2


class TestTag:
    def test_valid(self):
        t = Tag("Python")
        assert t.value == "python"

    def test_empty_rejected(self):
        with pytest.raises(ValueError):
            Tag("")

    def test_whitespace_rejected(self):
        with pytest.raises(ValueError):
            Tag("   ")

    def test_equality(self):
        assert Tag("python") == Tag("PYTHON")


class TestEntryType:
    def test_values(self):
        assert EntryType.Q_AND_A == "q-and-a"
        assert EntryType.GUIDE == "guide"
        assert EntryType.PATTERN == "pattern"
        assert EntryType.NOTE == "note"


class TestEntryFrontMatter:
    def test_valid_minimal(self):
        fm = EntryFrontMatter(
            id="abc12345",
            title="Test",
            type="q-and-a",
            tags=["python"],
            created="2025-01-15",
        )
        assert isinstance(fm.id, EntryId)
        assert isinstance(fm.tags[0], Tag)
        assert fm.type == EntryType.Q_AND_A

    def test_missing_required_field(self):
        with pytest.raises(Exception):
            EntryFrontMatter(
                id="abc12345",
                title="Test",
                # missing type
                tags=["python"],
                created="2025-01-15",
            )

    def test_empty_title_rejected(self):
        with pytest.raises(Exception):
            EntryFrontMatter(
                id="abc12345",
                title="   ",
                type="q-and-a",
                tags=["python"],
                created="2025-01-15",
            )

    def test_invalid_type_rejected(self):
        with pytest.raises(Exception):
            EntryFrontMatter(
                id="abc12345",
                title="Test",
                type="invalid",
                tags=["python"],
                created="2025-01-15",
            )

    def test_related_parsed(self):
        fm = EntryFrontMatter(
            id="abc12345",
            title="Test",
            type="note",
            tags=["python"],
            created="2025-01-15",
            related=["def67890"],
        )
        assert isinstance(fm.related[0], EntryId)
        assert fm.related[0].value == "def67890"

    def test_optional_fields(self):
        fm = EntryFrontMatter(
            id="abc12345",
            title="Test",
            type="guide",
            tags=["python"],
            created="2025-01-15",
            updated="2025-02-01",
            status="reviewed",
            difficulty="beginner",
            author="alice",
        )
        assert fm.status == EntryStatus.REVIEWED
        assert fm.difficulty == "beginner"
