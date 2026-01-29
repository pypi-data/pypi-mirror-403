# A basic document parsing and loading utility - Core

[![PyPI - Version](https://img.shields.io/pypi/v/docp-core?style=flat-square)](https://pypi.org/project/docp-core)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/docp-core?style=flat-square)](https://pypi.org/project/docp-core)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/docp-core?style=flat-square)](https://pypi.org/project/docp-core)
[![PyPI - Status](https://img.shields.io/pypi/status/docp-core?style=flat-square)](https://pypi.org/project/docp-core)
[![Static Badge](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](https://pypi.org/project/docp-core)
[![Static Badge](https://img.shields.io/badge/code_coverage-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-core)
[![Static Badge](https://img.shields.io/badge/pylint_analysis-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-core)
[![Documentation Status](https://readthedocs.org/projects/docp-core/badge/?version=latest&style=flat-square)](https://docp-core.readthedocs.io/en/latest/)
[![PyPI - License](https://img.shields.io/pypi/l/docp-core?style=flat-square)](https://opensource.org/license/gpl-3-0)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/docp-core?style=flat-square)](https://pypi.org/project/docp-core)

## Overview
The `docp-*` project suite is designed as a comprehensive (**doc**)ument \(**p**)arsing library. Built in CPython, it consolidates the capabilities of various lower-level libraries, offering a unified solution for parsing binary document structures.

The suite is extended by several sister projects, each providing unique functionality:

Project | Description                                                                               
|:---|:---
**docp-core** | Centralized core objects, functionality and settings.
**docp-parsers** | Parse binary documents (e.g. PDF, PPTX, etc.) into Python objects.                     
**docp-loaders** | Load a parsed document's embeddings into a Chroma vector database, for RAG-enabled LLM use.
**docp-docling** | Convert a PDF into Markdown format via wrappers to the `docling` libraries.
**docp-dbi** | Interfaces to document databases such as ChromaDB, and Neo4j (coming soon).

## Installation
To install `docp-core`, first activate your target virtual environment, then use `pip`:

```bash
pip install docp-core
```

For older releases, visit [PyPI][pypi-history] or the [GitHub Releases][giithub-releases] page.

## Using the Library
The documentation suite provides detailed explanations and usage examples for each importable module. For in-depth documentation, code examples, and source links, refer to the [Library API][api] page.

A **search** field is available in the left navigation bar to help you quickly locate specific modules or methods.

## Troubleshooting
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions, please open an issue on [GitHub][github].

[api]: https://docp-core.readthedocs.io/en/latest/
[github]: https://github.com/s3dev/docp-core
[github-releases]: https://github.com/s3dev/docp-core/releases
[pypi-history]: https://pypi.org/project/docp-core/#history
