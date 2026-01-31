# Workflow SDK Plugins

This directory contains plugins that extend `mistralai_workflows` with additional functionality.

## Context

It is helpful for developers of workflows to be able to **reuse** existing, curated pieces of logic, so that they do not have to start from scratch for each workflow they build. We want to provide such prefab pieces of business logic through a **plugin** mechanism.

### Examples of reusable logic that you may want to make available to others in a plugin

Reusable workflows:

- Execute a RAG pipeline that takes in some input, rewrites the input, queries a vector database, executes a BM25 search, reranks, and writes it output to storage
- Data ingestion workflow: basic pdfs / tables / audio chunks, etc.
- Agentic chat bot workflow with tools and handoffs
- Evaluation workflow
- High level orchestration workflows:
    - Wrapping around other workflows for evaluation
    - Running sub workflows in parallel
    - Fan out of a bundled input into separate sub-workflows based on a partitioning key

Reusable activities (the building blocks of a workflow):

- Execute an LLM completion
- Create an embedding for a piece of text or image
- Querying a vector database (e.g. Amazon S3 Vectors)
- Store or retrieve an object from BLOB storage (e.g. Amazon S3)

## How Plugins Work

Plugins use [PEP 420 namespace packages](https://peps.python.org/pep-0420/) combined with
`pkgutil.extend_path` to extend the `mistralai_workflows.plugins` namespace. This allows plugins to be:

1. **Separately installable** — Each plugin is its own Python package with its own `pyproject.toml`
2. **Imported under a unified namespace** — All plugins are imported as `mistralai_workflows.plugins.<name>`
3. **Cross-importable** — Plugins can import from each other (e.g., `mistralai_workflows.plugins.agents` can import from `mistralai_workflows.plugins.mistralai`)

## Creating Plugins

### Directory structure

Within the `workflow_sdk` package we follow this directory structure:

```
workflow_sdk/
├── mistralai_workflows/           # Main package
│   ├── __init__.py                # Main package init
│   ├── exports.py                 # All public exports (imported by plugins, see [Type checking and code completion](#type-checking-and-code-completion))
│   └── plugins/                   # Namespace package (NO __init__.py)
│
└── plugins/
    ├── agents/                    # Agents plugin package
    │   └── mistralai_workflows/
    │       ├── __init__.py        # To aid type checking and code completion, see [Type checking and code completion](#type-checking-and-code-completion)
    │       └── plugins/           # Namespace package (NO __init__.py)
    │           └── agents/
    │               ├── __init__.py  # Plugin's public API
    │               └── ...
    │
    └── mistralai/                 # Mistral plugin package
    |   └── mistralai_workflows/
    |       ├── __init__.py        # To aid type checking and code completion, see [Type checking and code completion](#type-checking-and-code-completion)
    |       └── plugins/           # Namespace package (NO __init__.py)
    |           └── mistralai/
    |               ├── __init__.py  # Plugin's public API
    |               └── ...
    └── .../                       # Other generally reusable plugins that are to be supported by Mistral AI's engineering team
```

Inside your plugin's directory (so e.g. in `workflow_sdk/plugins/<yourplugin>`) you follow the general `workflow_sdk` directory structure for plugins; i.e. your code must use the folder structure `mistralai_workflows/plugins/<yourplugin>`. Why? This is how [PEP420](https://peps.python.org/pep-0420/) namespace merging works.

### Type checking and code completion

During development, when you install your plugin (and `mistralai_workflows`) in _editable mode_, the [PEP420](https://peps.python.org/pep-0420/) feature that combines different directories on disk into one namespace, doesn't work reliably in typecheckers and IDEs (e.g. `mypy`, `pyright`).

As a work around, in your plugin's `mistralai_workflows/` directory (so e.g. in `workflow_sdk/plugins/<yourplugin>/mistralai_workflows/`) add an `__init__.py` that:

1. Extends the path for namespace package discovery
2. Re-exports from the core package for type checker compatibility

```python
# This file helps PyLance/VS Code and mypy resolve imports for our PEP 420 namespace mistralai_workflows/plugins.
# By re-exporting from the core package, this approach works with both PyRight (VS Code) and mypy (CI).
# See: https://github.com/microsoft/pylance-release/issues/7618
__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from mistralai_workflows.exports import *  # noqa: F403
from mistralai_workflows.exports import __all__ as __all__
```

After that, type checking and code completion should work!

**Important:** These `__init__.py` files are for local development only and must be excluded from
PyPI packages. If multiple plugins each ship their own `mistralai_workflows/__init__.py`, they would
conflict when installed together in non-editable mode: only one can "win" as they are merged on disk into the same dir. Each plugin's `pyproject.toml` should therefore have:

```toml
[tool.hatch.build.targets.wheel]
packages = ["mistralai_workflows"]
exclude = ["mistralai_workflows/__init__.py"]
```

### Running CI Checks

Each plugin should have their own CI checks, that you would run in the "usual" way with `invoke`:

```bash
cd workflow_sdk/plugins/myplugin
uvx invoke lint       # Linting with ruff
uvx invoke typecheck  # Type checking with mypy
uvx invoke tests      # Run pytest
```

See e.g. [./agents/tasks.py](./agents/tasks.py)
