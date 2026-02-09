"""Base36 ID generation."""

from __future__ import annotations

import secrets
import string

from lkr.models import EntryId

_ALPHABET = string.digits + string.ascii_lowercase  # 0-9a-z


def encode_base36(n: int) -> str:
    """Encode a non-negative integer to a base36 string."""
    if n < 0:
        raise ValueError("Cannot encode negative number")
    if n == 0:
        return "0"
    chars: list[str] = []
    while n > 0:
        n, remainder = divmod(n, 36)
        chars.append(_ALPHABET[remainder])
    return "".join(reversed(chars))


def decode_base36(s: str) -> int:
    """Decode a base36 string to an integer."""
    return int(s, 36)


def generate_id() -> EntryId:
    """Generate a random 8-char base36 ID from 5 random bytes."""
    random_int = int.from_bytes(secrets.token_bytes(5), "big")
    raw = encode_base36(random_int).ljust(8, "0")[:8]
    return EntryId(raw)


def is_valid_base36(s: str) -> bool:
    """Check if string is valid base36 (lowercase alphanumeric, 1-8 chars)."""
    return bool(s) and len(s) <= 8 and all(c in _ALPHABET for c in s)
