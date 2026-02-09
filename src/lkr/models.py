"""Domain models — parse, don't validate."""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Value objects (newtypes)
# ---------------------------------------------------------------------------

_BASE36_RE = re.compile(r"^[0-9a-z]{1,8}$")


class EntryId:
    """Validated base36 ID (1-8 lowercase alphanumeric characters).

    Once constructed, the ID is guaranteed valid. Use .prefix for sharding.
    """

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        v = raw.strip().lower()
        if not _BASE36_RE.match(v):
            raise ValueError(
                f"Invalid entry ID {raw!r}: must be 1-8 lowercase alphanumeric"
            )
        self._value = v

    @property
    def value(self) -> str:
        return self._value

    @property
    def prefix(self) -> str:
        return self._value[:2]

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"EntryId({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EntryId):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


class Tag:
    """Normalized tag (lowercase, non-empty)."""

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        v = raw.strip().lower()
        if not v:
            raise ValueError("Tag cannot be empty")
        self._value = v

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Tag({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Tag):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


class EntryType(StrEnum):
    Q_AND_A = "q-and-a"
    GUIDE = "guide"
    PATTERN = "pattern"
    NOTE = "note"


class EntryStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    OUTDATED = "outdated"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class EntryFrontMatter(BaseModel):
    """YAML front matter for a knowledge entry."""

    model_config = {"arbitrary_types_allowed": True}

    id: EntryId
    title: str
    type: EntryType
    tags: list[Tag]
    created: date
    updated: date | None = None
    status: EntryStatus | None = None
    difficulty: str | None = None
    author: str | None = None
    related: list[EntryId] | None = None
    source: dict[str, str] | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _parse_id(cls, v: Any) -> EntryId:
        if isinstance(v, EntryId):
            return v
        return EntryId(str(v))

    @field_validator("tags", mode="before")
    @classmethod
    def _parse_tags(cls, v: Any) -> list[Tag]:
        if not isinstance(v, list):
            raise ValueError("tags must be a list")
        return [t if isinstance(t, Tag) else Tag(str(t)) for t in v]

    @field_validator("related", mode="before")
    @classmethod
    def _parse_related(cls, v: Any) -> list[EntryId] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("related must be a list")
        return [r if isinstance(r, EntryId) else EntryId(str(r)) for r in v]

    @field_validator("created", "updated", mode="before")
    @classmethod
    def _parse_date(cls, v: Any) -> date | None:
        if v is None:
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    @model_validator(mode="after")
    def _check_title(self) -> "EntryFrontMatter":
        if not self.title.strip():
            raise ValueError("title cannot be empty")
        return self


class Entry(BaseModel):
    """A fully parsed knowledge entry."""

    model_config = {"arbitrary_types_allowed": True}

    front_matter: EntryFrontMatter
    body: str
    source_path: Path | None = None


class RepoConfig(BaseModel):
    """Schema for .knowledge/config.yaml."""

    version: str = "0.1.0"
    name: str = ""
    description: str = ""


class IndexEntry(BaseModel):
    """Single entry in the generated index."""

    model_config = {"arbitrary_types_allowed": True}

    id: str
    path: str
    title: str
    type: str
    tags: list[str]
    status: str | None = None
    created: str
    updated: str | None = None


class Index(BaseModel):
    """Full generated index."""

    generated: str
    entry_count: int
    entries: list[IndexEntry]
    tag_index: dict[str, list[str]]
    type_index: dict[str, list[str]]
