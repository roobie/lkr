"""Exception hierarchy for lkr."""


class KnowledgeError(Exception):
    """Base exception for all lkr errors."""


class RepoNotFoundError(KnowledgeError):
    """No .knowledge/config.yaml found walking up from cwd."""


class EntryParseError(KnowledgeError):
    """Entry file failed to parse."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")


class EntryNotFoundError(KnowledgeError):
    """Entry ID does not resolve to a file on disk."""

    def __init__(self, entry_id: str) -> None:
        self.entry_id = entry_id
        super().__init__(f"Entry not found: {entry_id}")
