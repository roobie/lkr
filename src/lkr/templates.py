"""Entry body templates by type."""

from __future__ import annotations

from lkr.models import EntryType

TEMPLATES: dict[EntryType, str] = {
    EntryType.Q_AND_A: """\
## Question

<!-- What specific problem or question does this address? -->

## Answers

### Answer 1

<!-- Describe the solution -->

## Common Pitfalls

<!-- What mistakes do people commonly make? -->

## See Also

<!-- Related entries or external links -->
""",
    EntryType.GUIDE: """\
## Overview

<!-- Brief description of what this guide covers -->

## Prerequisites

<!-- What does the reader need to know/have? -->

## Steps

### Step 1

<!-- First step -->

### Step 2

<!-- Second step -->

## Troubleshooting

<!-- Common issues and how to resolve them -->
""",
    EntryType.PATTERN: """\
## Problem

<!-- What problem does this pattern solve? -->

## Solution

<!-- Describe the pattern -->

## When to Use

<!-- When is this pattern appropriate? -->

## Trade-offs

<!-- What are the pros and cons? -->
""",
    EntryType.NOTE: """\
## Summary

<!-- Brief summary of this note -->

## Details

<!-- Detailed content -->
""",
}


def get_template(entry_type: EntryType) -> str:
    """Return the body template for the given entry type."""
    return TEMPLATES[entry_type]
