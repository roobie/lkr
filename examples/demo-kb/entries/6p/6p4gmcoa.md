---
author: alice
created: '2026-02-10'
id: 6p4gmcoa
status: reviewed
tags:
- architecture
- python
- design-patterns
title: Repository Pattern for Data Access
type: pattern
---

## Problem

Application code becomes tightly coupled to database queries and ORM calls,
making it hard to test, swap storage backends, or reason about data access
boundaries.

## Solution

Introduce a **Repository** class that encapsulates all data access logic for a
given aggregate. The rest of the application depends on the repository
interface, not on the database directly.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def list_all(self) -> list[User]: ...


class SqlUserRepository(UserRepository):
    def __init__(self, connection):
        self._conn = connection

    def get(self, user_id: int) -> User | None:
        row = self._conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User(*row) if row else None

    def save(self, user: User) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
            (user.id, user.name, user.email),
        )

    def list_all(self) -> list[User]:
        rows = self._conn.execute("SELECT id, name, email FROM users").fetchall()
        return [User(*r) for r in rows]
```

For tests, use an in-memory implementation:

```python
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: dict[int, User] = {}

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def list_all(self) -> list[User]:
        return list(self._users.values())
```

## When to Use

- When business logic needs to be tested without a real database
- When you may need to swap storage backends (SQL, NoSQL, file, API)
- When data access is complex enough that scattering queries throughout
  service code would be confusing

## Trade-offs

**Pros:**
- Clean separation between domain logic and persistence
- Easy to test with in-memory fakes
- Explicit data access boundaries

**Cons:**
- Extra abstraction layer adds boilerplate
- Can be overkill for simple CRUD apps
- ORM features like lazy loading may not map cleanly to the repository interface
