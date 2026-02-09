---
author: bob
created: '2026-02-10'
id: 1qtmorq2
status: reviewed
tags:
- python
- concurrency
- performance
title: Python GIL Explained
type: note
related:
- 68tfu7mo
---

## Summary

The **Global Interpreter Lock (GIL)** is a mutex in CPython that allows only
one thread to execute Python bytecode at a time. It simplifies memory
management but limits true parallelism for CPU-bound tasks.

## Details

### What the GIL does

- Protects CPython's reference counting garbage collector from race conditions
- Ensures that only one thread runs Python bytecode at any given moment
- Is released during I/O operations (file reads, network calls, `time.sleep`)

### When the GIL matters

| Workload | GIL impact | Recommendation |
|----------|-----------|----------------|
| I/O-bound (web requests, file I/O) | Minimal — GIL is released during I/O | Use `threading` or `asyncio` |
| CPU-bound (math, parsing, compression) | Significant — threads don't parallelize | Use `multiprocessing` or C extensions |
| Mixed | Depends on ratio | Profile first, then decide |

### Workarounds for CPU-bound parallelism

1. **`multiprocessing`** — spawns separate processes, each with its own GIL
2. **C extensions** — libraries like NumPy release the GIL during computation
3. **`concurrent.futures.ProcessPoolExecutor`** — high-level API over multiprocessing
4. **Free-threaded Python (3.13+)** — experimental `--disable-gil` build

### Quick example

```python
from concurrent.futures import ProcessPoolExecutor
import math

def is_prime(n):
    return n > 1 and all(n % i for i in range(2, int(math.sqrt(n)) + 1))

# CPU-bound work — use processes, not threads
with ProcessPoolExecutor() as pool:
    results = list(pool.map(is_prime, range(100_000)))
```
