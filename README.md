# lkr

A git-native, LLM-ready knowledge repository manager. Store programming
knowledge as Markdown entries with structured YAML front matter, sharded
into directories by base36 ID.

## Why

- **Git is the platform** — version control, collaboration, and distribution
  are built in. No database, no server, no vendor lock-in.
- **Human and machine readable** — plain Markdown for people, structured
  metadata for tools and LLMs.
- **Offline-first** — everything works locally. Search, validate, and create
  entries without a network connection.

## Install

Requires Python 3.12+.

```bash
uv tool install git+https://github.com/your-org/lkr
```

Or for development:

```bash
git clone https://github.com/your-org/lkr
cd lkr
uv sync
```

## Quick start

```bash
# Initialize a new knowledge repo
k init "My Knowledge Base"

# Create entries (types: q-and-a, guide, pattern, note)
k new q-and-a "How to fix ImportError" -t python -t troubleshooting
k new guide "Getting Started with Docker" -t docker -t devops
k new note "Python GIL Explained" -t python -t concurrency

# Search across all entries
k search "docker"
k search "import" -t python          # filter by tag
k search "pattern" --type pattern    # filter by entry type

# View entries
k get <id>                           # show summary
k cat <id>                           # print raw markdown

# Validate and index
k validate                           # check all entries for errors
k index                              # generate .knowledge/index.json
```

## Repository structure

After `k init`, your repo looks like this:

```
my-knowledge-base/
├── entries/
│   ├── fv/
│   │   └── fvb2iq3a.md             # sharded by first 2 chars of ID
│   ├── k3/
│   │   └── k3mnwx00.md
│   └── ...
├── .knowledge/
│   ├── config.yaml                  # repo settings
│   └── index.json                   # auto-generated (git-ignored)
├── README.md
└── .gitignore
```

## Entry format

Each entry is a Markdown file with YAML front matter:

```markdown
---
id: "fvb2iq3a"
title: "How to fix ImportError in Python"
type: q-and-a
tags:
  - python
  - import
  - troubleshooting
created: 2025-01-15
status: reviewed
author: alice
related:
  - k3mnwx00
---

## Question

How do I fix `ImportError: No module named X`?

## Answers

### Answer 1: Install the missing package
...
```

**Required fields:** `id`, `title`, `type`, `tags`, `created`

**Optional fields:** `updated`, `status` (draft/reviewed/outdated),
`difficulty`, `author`, `related`, `source`

**Entry types:** `q-and-a`, `guide`, `pattern`, `note` — each generates a
body template with appropriate sections.

## Entry types

| Type      | Purpose                           | Sections                                        |
|-----------|-----------------------------------|-------------------------------------------------|
| `q-and-a` | Specific problem with solution    | Question, Answers, Common Pitfalls, See Also    |
| `guide`   | Step-by-step tutorial             | Overview, Prerequisites, Steps, Troubleshooting |
| `pattern` | Reusable solution or anti-pattern | Problem, Solution, When to Use, Trade-offs      |
| `note`    | Quick reference or concept        | Summary, Details                                |

## Commands

| Command                | Description                                        |
|------------------------|----------------------------------------------------|
| `k init <name>`        | Initialize a new knowledge repository              |
| `k new <type> <title>` | Create a new entry with generated ID               |
| `k search <query>`     | Full-text search (uses ripgrep if available)       |
| `k get <id>`           | Show entry summary                                 |
| `k cat <id>`           | Print raw entry to stdout                          |
| `k validate`           | Check all entries for schema and structural errors |
| `k index`              | Generate `.knowledge/index.json`                   |

The CLI is available as both `k` and `lkr`.

## ID system

Entry IDs are 8-character base36 strings (0-9, a-z) generated from 5 random
bytes. The first 2 characters determine the shard directory, giving 1,296
possible prefixes (36 x 36). Collision probability is roughly 1 in a trillion.

## Example

See [`examples/demo-kb/`](examples/demo-kb/) for a working knowledge repo
with four entries covering all entry types.

## Development

```bash
uv sync
uv run pytest tests/ -v
```

## License

Apache-2.0
