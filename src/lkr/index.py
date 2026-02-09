"""Index generation for .knowledge/index.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from lkr.models import Index, IndexEntry

if TYPE_CHECKING:
    from lkr.repo import KnowledgeRepo


def build_index(repo: "KnowledgeRepo") -> Index:
    """Scan all entries and build a typed Index."""
    entries_list: list[IndexEntry] = []
    tag_index: dict[str, list[str]] = {}
    type_index: dict[str, list[str]] = {}

    for entry in repo.iter_entries():
        fm = entry.front_matter
        id_str = fm.id.value

        idx_entry = IndexEntry(
            id=id_str,
            path=str(entry.source_path.relative_to(repo.root)) if entry.source_path else "",
            title=fm.title,
            type=fm.type.value,
            tags=[t.value for t in fm.tags],
            status=fm.status.value if fm.status else None,
            created=fm.created.isoformat(),
            updated=fm.updated.isoformat() if fm.updated else None,
        )
        entries_list.append(idx_entry)

        # Tag index
        for tag in fm.tags:
            tag_index.setdefault(tag.value, []).append(id_str)

        # Type index
        type_index.setdefault(fm.type.value, []).append(id_str)

    return Index(
        generated=datetime.now(timezone.utc).isoformat(),
        entry_count=len(entries_list),
        entries=entries_list,
        tag_index=tag_index,
        type_index=type_index,
    )


def write_index(repo: "KnowledgeRepo") -> Index:
    """Build index and write to .knowledge/index.json."""
    index = build_index(repo)
    index_path = repo.knowledge_dir / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index.model_dump(), indent=2) + "\n")
    return index
