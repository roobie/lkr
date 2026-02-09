# LKR Design Document

> Design document for the `lkr` CLI tool — a git-native, LLM-ready knowledge
> repository manager.

## 1. Architecture Overview

LKR follows a layered architecture with strict parsing boundaries:

```
┌─────────────────────────────────────┐
│            CLI Layer (click)         │  ← User input parsing boundary
├─────────────────────────────────────┤
│          Domain Services             │  ← Operates on typed objects only
│  repo.py │ entry.py │ validate.py   │
│  index.py│ search.py│ templates.py  │
├─────────────────────────────────────┤
│          Domain Models               │  ← "Parse, don't validate"
│  models.py │ idgen.py │ errors.py   │
├─────────────────────────────────────┤
│        Infrastructure                │
│  console.py (Rich) │ filesystem     │
└─────────────────────────────────────┘
```

### Core Principle: Parse, Don't Validate

Raw data (YAML dicts, file paths, CLI strings) is parsed into rich typed
objects **at the boundary**. Once parsed, the rest of the codebase works
exclusively with these typed objects. Invalid states are unrepresentable.

Parsing boundaries:
- `EntryId(raw_string)` — validates base36 format at construction
- `Tag(raw_string)` — normalizes and validates at construction
- `parse_entry(path)` — reads file, returns fully typed `Entry` or raises
- `KnowledgeRepo.load_config()` — parses config YAML into `RepoConfig`
- `build_index(repo)` — constructs typed `Index` from parsed entries
- CLI command handlers — parse raw user input into domain types

## 2. Module Design

### 2.1 `lkr.errors` — Exception Hierarchy

```python
class KnowledgeError(Exception):
    """Base exception for all lkr errors."""

class RepoNotFoundError(KnowledgeError):
    """No .knowledge/config.yaml found walking up from cwd."""

class EntryParseError(KnowledgeError):
    """Entry file failed to parse (bad YAML, missing fields, etc.)."""

class EntryNotFoundError(KnowledgeError):
    """Entry ID does not resolve to a file on disk."""
```

All exceptions inherit from `KnowledgeError` so the CLI can catch them
uniformly and display user-friendly messages.

### 2.2 `lkr.models` — Domain Types

#### Newtypes (Value Objects)

These wrap primitive types and enforce invariants at construction time.

```python
class EntryId:
    """Wraps a validated base36 ID string (1-8 lowercase alphanumeric).

    Properties:
        value: str — the raw ID string
        prefix: str — first 2 chars, used for directory sharding
    """
    def __init__(self, raw: str) -> None: ...

class Tag:
    """Wraps a normalized tag string (lowercase, non-empty).

    Construction normalizes to lowercase and strips whitespace.
    Rejects empty/whitespace-only values.
    """
    def __init__(self, raw: str) -> None: ...
```

#### Enums

```python
class EntryType(StrEnum):
    Q_AND_A = "q-and-a"
    GUIDE = "guide"
    PATTERN = "pattern"
    NOTE = "note"

class EntryStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    OUTDATED = "outdated"
```

#### Pydantic Models

```python
class EntryFrontMatter(BaseModel):
    """Required: id, title, type, tags, created.
    Optional: updated, status, difficulty, author, related, source."""

class Entry(BaseModel):
    """front_matter + body + source_path. Constructed only by parse_entry()."""

class RepoConfig(BaseModel):
    """Schema for .knowledge/config.yaml."""

class IndexEntry(BaseModel):
    """Single entry in the index."""

class Index(BaseModel):
    """Full index: entries list + tag_index + type_index + generated timestamp."""
```

### 2.3 `lkr.idgen` — ID Generation

IDs are base36-encoded random values. 5 random bytes provide ~1.1 trillion
possible values, encoded to exactly 8 base36 characters.

```python
def encode_base36(n: int) -> str:
    """Encode non-negative integer to base36 string (0-9, a-z)."""

def decode_base36(s: str) -> int:
    """Decode base36 string to integer."""

def generate_id() -> EntryId:
    """Generate a random 8-char base36 ID from 5 random bytes.

    Algorithm:
        1. Generate 5 random bytes via secrets.token_bytes(5)
        2. Convert to integer (big-endian)
        3. Encode as base36
        4. Pad/truncate to exactly 8 characters
        5. Wrap in EntryId (validates format)
    """

def is_valid_base36(s: str) -> bool:
    """Check if string is valid base36 (lowercase alphanumeric)."""
```

**Why 5 bytes?**
- 5 bytes = 40 bits = max value 1,099,511,627,775
- base36 encoding: `encode_base36(1099511627775)` = `"hzzzzzzy"` (8 chars)
- Truncating to 8 chars gives full 8-character IDs
- Collision probability: ~1 in 2^40 ≈ 1 in 1 trillion

**Sharding:**
- First 2 characters of the ID determine the directory
- 36 × 36 = 1,296 possible shard directories
- Entry `fvb2iq3a` lives at `entries/fv/fvb2iq3a.md`

### 2.4 `lkr.console` — Rich Output Helpers

```python
console: Console  # Module-level singleton

def print_success(message: str) -> None: ...
def print_error(message: str) -> None: ...
def print_warning(message: str) -> None: ...
def print_entry_summary(entry: Entry) -> None: ...
def print_validation_report(report: ValidationReport) -> None: ...
def print_search_results(results: list[SearchResult]) -> None: ...
```

Uses Rich for colored output, tables, and panels. All output goes through
these helpers so formatting is consistent.

### 2.5 `lkr.templates` — Entry Body Templates

Each entry type has a Markdown body template:

```python
TEMPLATES: dict[EntryType, str] = {
    EntryType.Q_AND_A: "## Question\n\n...\n\n## Answers\n\n...",
    EntryType.GUIDE: "## Overview\n\n...\n\n## Prerequisites\n\n...",
    EntryType.PATTERN: "## Problem\n\n...\n\n## Solution\n\n...",
    EntryType.NOTE: "## Summary\n\n...\n\n## Details\n\n...",
}

def get_template(entry_type: EntryType) -> str:
    """Return the body template for the given entry type."""
```

### 2.6 `lkr.entry` — Entry CRUD

```python
def parse_entry(path: Path) -> Entry:
    """THE parsing boundary for entries.

    Reads raw markdown file, splits YAML front matter from body,
    parses all fields into typed objects (EntryId, Tag, EntryType, etc.),
    and returns a fully valid Entry.

    Raises EntryParseError if anything is wrong.
    No downstream code ever re-validates.
    """

def serialize_entry(entry: Entry) -> str:
    """Convert Entry back to markdown string with YAML front matter."""

def write_entry(entry: Entry, path: Path) -> None:
    """Write serialized entry to disk. Creates parent directories."""

def create_entry(
    entry_type: EntryType,
    title: str,
    tags: list[str],
    author: str | None = None,
) -> Entry:
    """Create a new Entry with generated ID and body template.

    This is a parsing boundary: raw strings are parsed into typed objects.
    """
```

### 2.7 `lkr.repo` — Repository Operations

```python
class KnowledgeRepo:
    """Represents a discovered knowledge repository on disk.

    Attributes:
        root: Path — repository root directory
        entries_dir: Path — root / "entries"
        knowledge_dir: Path — root / ".knowledge"
    """

    @classmethod
    def discover(cls, start: Path | None = None) -> "KnowledgeRepo":
        """Walk up from start (default: cwd) looking for .knowledge/config.yaml.
        Raises RepoNotFoundError if not found."""

    @classmethod
    def init(cls, path: Path, name: str) -> "KnowledgeRepo":
        """Initialize a new knowledge repo at path.
        Creates: entries/, .knowledge/config.yaml, README.md, .gitignore additions."""

    def load_config(self) -> RepoConfig:
        """Parse .knowledge/config.yaml into RepoConfig."""

    def entry_path(self, entry_id: EntryId) -> Path:
        """Compute path for entry: entries/{prefix}/{id}.md
        Accepts EntryId (not raw str) — callers must parse first."""

    def iter_entries(self) -> Iterator[Entry]:
        """Parse all .md files under entries/, yielding Entry objects.
        Silently skips files that fail to parse (logs warning)."""

    def resolve_entry(self, raw_id: str) -> Entry:
        """Parsing boundary for CLI: parse raw string to EntryId,
        locate file, parse to Entry. Raises on failure."""
```

### 2.8 `lkr.validate` — Repo Validation

Validation is a **reporting** tool, not a gatekeeper. It attempts to parse
every entry and collects what fails. The parsing itself (in `parse_entry`)
enforces correctness.

```python
@dataclass
class ValidationIssue:
    level: str  # "error" or "warning"
    file: str
    message: str

@dataclass
class ValidationReport:
    issues: list[ValidationIssue]
    entries_checked: int
    errors: int
    warnings: int

    @property
    def is_clean(self) -> bool: ...

def validate_repo(repo: KnowledgeRepo) -> ValidationReport:
    """Run all validation checks and return a report.

    Checks:
    1. Schema compliance — entries that fail parse_entry()
    2. Uniqueness — duplicate EntryIds
    3. References — related IDs exist
    4. File naming — {id}.md matches front matter
    5. Directory structure — parent dir = first 2 chars of ID
    6. Warnings — old drafts (>30d), stale entries (>180d)
    """
```

### 2.9 `lkr.index` — Index Generation

```python
def build_index(repo: KnowledgeRepo) -> Index:
    """Scan all entries, build Index with:
    - entries: list of IndexEntry (id, path, title, type, tags, etc.)
    - tag_index: dict[str, list[str]] mapping tags to entry IDs
    - type_index: dict[str, list[str]] mapping types to entry IDs
    - generated: ISO timestamp
    """

def write_index(repo: KnowledgeRepo) -> Index:
    """Build index and write to .knowledge/index.json."""
```

### 2.10 `lkr.search` — Full-Text Search

```python
@dataclass
class SearchResult:
    entry_id: str
    title: str
    path: str
    matches: list[str]  # matching lines

def search(
    query: str,
    entries_dir: Path,
    tag: str | None = None,
    entry_type: str | None = None,
) -> list[SearchResult]:
    """Dispatch to ripgrep (if available) or Python fallback."""

def search_ripgrep(
    query: str, entries_dir: Path
) -> list[SearchResult]:
    """Shell out to rg for fast search."""

def search_python(
    query: str, entries_dir: Path
) -> list[SearchResult]:
    """Pure-Python fallback: case-insensitive substring match."""

def has_ripgrep() -> bool:
    """Check if rg is on PATH."""
```

### 2.11 `lkr.cli` — Click Commands

```python
@click.group()
def cli():
    """LKR — Knowledge Repository Manager."""

@cli.command()
@click.argument("name")
def init(name: str):
    """Initialize a new knowledge repository."""

@cli.command()
@click.argument("entry_type", type=click.Choice([...]))
@click.argument("title")
@click.option("-t", "--tag", multiple=True)
@click.option("-a", "--author")
def new(entry_type: str, title: str, tag: tuple[str, ...], author: str | None):
    """Create a new entry."""

@cli.command()
@click.argument("query")
@click.option("-t", "--tag")
@click.option("--type", "entry_type")
def search(query: str, tag: str | None, entry_type: str | None):
    """Search entries."""

@cli.command()
@click.argument("entry_id")
def get(entry_id: str):
    """Show entry summary."""

@cli.command()
@click.argument("entry_id")
def cat(entry_id: str):
    """Print raw entry to stdout."""

@cli.command()
def validate():
    """Validate all entries."""

@cli.command()
def index():
    """Generate .knowledge/index.json."""
```

All commands use lazy imports for fast startup. An error handler decorator
catches `KnowledgeError` subtypes and prints user-friendly messages via Rich.

## 3. Data Flow Examples

### Creating a New Entry

```
User: k new q-and-a "How to fix X" -t python -t error

CLI parses args → create_entry(
    entry_type=EntryType.Q_AND_A,   # parsed from string
    title="How to fix X",
    tags=["python", "error"],       # will be parsed to Tag objects
)

create_entry:
    1. generate_id() → EntryId("fvb2iq3a")     # validated at construction
    2. Tags parsed: [Tag("python"), Tag("error")] # validated at construction
    3. Template selected for Q_AND_A
    4. Entry constructed with all typed fields
    5. write_entry(entry, repo.entry_path(entry.front_matter.id))
       → writes to entries/fv/fvb2iq3a.md
```

### Validating the Repo

```
User: k validate

CLI:
    1. repo = KnowledgeRepo.discover()
    2. report = validate_repo(repo)
       - For each .md file in entries/:
         a. Try parse_entry() — if fails, record schema error
         b. Collect all parsed entries
       - Check for duplicate IDs
       - Check related[] references resolve
       - Check filename matches ID
       - Check directory matches ID prefix
       - Check for old drafts / stale entries (warnings)
    3. print_validation_report(report)
```

## 4. Repository Layout on Disk

```
my-knowledge-base/
├── entries/
│   ├── fv/
│   │   └── fvb2iq3a.md
│   ├── k3/
│   │   └── k3mnwx00.md
│   └── ...
├── .knowledge/
│   ├── config.yaml          # Repo settings
│   └── index.json           # Auto-generated (git-ignored)
├── README.md
└── .gitignore
```

### config.yaml Schema

```yaml
version: "0.1.0"
name: "My Knowledge Base"
description: "Optional description"
```

### index.json Schema

```json
{
  "generated": "2025-01-15T10:30:00Z",
  "entry_count": 42,
  "entries": [
    {
      "id": "fvb2iq3a",
      "path": "entries/fv/fvb2iq3a.md",
      "title": "How to fix ImportError",
      "type": "q-and-a",
      "tags": ["python", "import"],
      "status": "reviewed",
      "created": "2025-01-15",
      "updated": "2025-02-09"
    }
  ],
  "tag_index": {
    "python": ["fvb2iq3a", "k3mnwx00"],
    "import": ["fvb2iq3a"]
  },
  "type_index": {
    "q-and-a": ["fvb2iq3a"],
    "guide": ["k3mnwx00"]
  }
}
```

## 5. Entry Format

```markdown
---
id: "fvb2iq3a"
title: "Fixing ImportError: No module named X"
type: q-and-a
tags:
  - python
  - import
  - troubleshooting
created: 2025-01-15
updated: 2025-02-09
status: reviewed
difficulty: beginner
author: alice
related:
  - k3mnwx00
---

## Question

How do I fix `ImportError: No module named X` in Python?

## Answers

### Answer 1: Wrong Virtual Environment

...
```

## 6. Validation Rules Detail

| # | Check      | Level   | Description                                          |
|---|------------|---------|------------------------------------------------------|
| 1 | Schema     | error   | Entry fails `parse_entry()` — missing/invalid fields |
| 2 | Unique IDs | error   | Two entries share the same `id` value                |
| 3 | References | error   | `related` contains an ID that doesn't exist          |
| 4 | Filename   | error   | File is `abc.md` but front matter `id` is `xyz`      |
| 5 | Directory  | error   | Entry in `entries/ab/` but ID starts with `cd`       |
| 6 | Old draft  | warning | Status is `draft` and created > 30 days ago          |
| 7 | Stale      | warning | No `updated` and created > 180 days ago              |

## 7. Error Handling Strategy

Errors are categorized by recoverability:

- **User errors** (wrong ID, missing repo): caught at CLI level, printed via
  Rich with helpful message and exit code 1.
- **Parse errors** (bad YAML, invalid fields): `EntryParseError` with file
  path and specific issue.
- **System errors** (disk full, permissions): allowed to propagate as-is.

The CLI uses a decorator pattern:

```python
def handle_errors(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KnowledgeError as e:
            print_error(str(e))
            raise SystemExit(1)
    return wrapper
```

## 8. Testing Strategy

### Unit Tests

- **test_idgen.py**: encode/decode round-trip, generate returns valid IDs,
  uniqueness over 1000 generations, validation edge cases
- **test_models.py**: Pydantic validation for valid/invalid inputs, enum
  values, date parsing, EntryId/Tag construction
- **test_entry.py**: parse/serialize round-trip, missing fields, extra fields,
  template application

### Integration Tests

- **test_validate.py**: Each validation rule with purpose-built fixtures
- **test_index.py**: Correct entry counts, tag/type mapping accuracy
- **test_search.py**: Python fallback search, tag/type filters, empty results

### CLI Tests

- **test_cli.py**: Click CliRunner for all commands. Tests init creates
  structure, new creates valid entry, cat outputs content, validate reports
  errors, index generates JSON, search finds entries.

### Fixtures

```python
@pytest.fixture
def tmp_repo(tmp_path):
    """Initialize a knowledge repo in a temp directory."""

@pytest.fixture
def sample_entry_text():
    """Return valid entry markdown string."""

@pytest.fixture
def populated_repo(tmp_repo):
    """A repo with 3 diverse entries pre-created."""
```

## 9. Dependencies

| Package            | Purpose               | Version |
|--------------------|-----------------------|---------|
| click              | CLI framework         | >=8.1   |
| pyyaml             | YAML parsing          | >=6.0   |
| python-frontmatter | Markdown front matter | >=1.1   |
| rich               | Terminal formatting   | >=13.0  |
| pydantic           | Data models           | >=2.5   |

Dev dependencies: pytest, pytest-cov, pytest-xdist, ruff, ty

## 10. Future Considerations

Not in scope for v0.1.0 but worth noting:

- **Export formats**: HTML, PDF, static site generation
- **Import**: From existing markdown collections, wikis
- **Merge conflict resolution**: Custom git merge driver for entries
- **Editor integration**: LSP for entry authoring
- **Remote sync**: Beyond plain git push/pull
