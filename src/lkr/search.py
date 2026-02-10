"""Full-text search with ripgrep fallback to Python."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import frontmatter


@dataclass
class SearchResult:
    entry_id: str
    title: str
    path: str
    matches: list[str]


def has_ripgrep() -> bool:
    """Check if rg is on PATH."""
    try:
        subprocess.run(
            ["rg", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def search(
    query: str,
    entries_dir: Path,
    tag: str | None = None,
    entry_type: str | None = None,
) -> list[SearchResult]:
    """Search entries, dispatching to ripgrep or Python fallback."""
    if has_ripgrep():
        results = search_ripgrep(query, entries_dir)
    else:
        results = search_python(query, entries_dir)

    # Post-filter by tag/type
    if tag or entry_type:
        results = _filter_results(results, entries_dir, tag, entry_type)

    return results


def search_ripgrep(query: str, entries_dir: Path) -> list[SearchResult]:
    """Use ripgrep for fast search."""
    try:
        proc = subprocess.run(
            ["rg", "--files-with-matches", "--ignore-case", query, str(entries_dir)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return search_python(query, entries_dir)

    if not proc.stdout.strip():
        return []

    results: list[SearchResult] = []
    for file_path in proc.stdout.strip().splitlines():
        path = Path(file_path)
        if not path.name.endswith(".md"):
            continue
        result = _make_result(path, query)
        if result:
            results.append(result)

    return results


def search_python(query: str, entries_dir: Path) -> list[SearchResult]:
    """Pure-Python fallback: case-insensitive substring match."""
    results: list[SearchResult] = []
    if not entries_dir.exists():
        return results

    query_lower = query.lower()
    for md_file in sorted(entries_dir.rglob("*.md")):
        try:
            content = md_file.read_text()
        except OSError:
            continue

        if query_lower in content.lower():
            result = _make_result(md_file, query)
            if result:
                results.append(result)

    return results


def _make_result(path: Path, query: str) -> SearchResult | None:
    """Build a SearchResult from a matching file."""
    try:
        post = frontmatter.load(str(path))
    except Exception:
        return None

    entry_id = post.metadata.get("id", path.stem)
    title = post.metadata.get("title", path.stem)

    # Collect matching lines
    query_lower = query.lower()
    matches = [
        line for line in post.content.splitlines() if query_lower in line.lower()
    ]

    return SearchResult(
        entry_id=str(entry_id),
        title=str(title),
        path=str(path),
        matches=matches,
    )


def _filter_results(
    results: list[SearchResult],
    entries_dir: Path,
    tag: str | None,
    entry_type: str | None,
) -> list[SearchResult]:
    """Post-filter search results by tag and/or type."""
    filtered: list[SearchResult] = []
    for r in results:
        try:
            post = frontmatter.load(r.path)
        except Exception:
            continue

        if tag:
            tags = post.metadata.get("tags", [])
            if tag.lower() not in [str(t).lower() for t in tags]:
                continue

        if entry_type:
            if post.metadata.get("type") != entry_type:
                continue

        filtered.append(r)

    return filtered
