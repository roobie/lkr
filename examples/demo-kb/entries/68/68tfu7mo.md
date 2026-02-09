---
author: alice
created: '2026-02-10'
id: 68tfu7mo
status: reviewed
tags:
- python
- import
- troubleshooting
title: How to fix Python ImportError
type: q-and-a
related:
- 1qtmorq2
---

## Question

How do I fix `ImportError: No module named X` when running a Python script?

## Answers

### Answer 1: Install the missing package

The most common cause is that the package simply isn't installed in your
current environment.

```bash
pip install X
# or with uv:
uv pip install X
```

### Answer 2: Wrong virtual environment

You may have the package installed in a different virtual environment.
Check which Python you're using:

```bash
which python
python -c "import sys; print(sys.prefix)"
```

Activate the correct environment:

```bash
source .venv/bin/activate
```

### Answer 3: Module path not on sys.path

If you're importing from a local package, make sure the directory is on
Python's module search path:

```python
import sys
sys.path.insert(0, "/path/to/your/project")
```

Better yet, install your project in editable mode:

```bash
pip install -e .
```

## Common Pitfalls

- Installing packages globally instead of in a virtual environment
- Confusing the PyPI package name with the import name (e.g., `pip install
  Pillow` but `import PIL`)
- Forgetting to activate the virtual environment after opening a new terminal

## See Also

- Python docs: [The import system](https://docs.python.org/3/reference/import.html)
