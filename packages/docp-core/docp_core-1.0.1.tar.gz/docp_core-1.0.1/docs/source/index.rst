===============================
docp-core Library Documentation
===============================

.. contents:: Page Contents
    :local:
    :depth: 1

Overview
========
The ``docp-*`` project suite is designed as a comprehensive (**doc**)ument
(**p**)arsing library. Built in CPython, it consolidates the capabilities
of various lower-level libraries, offering a unified solution for parsing
binary document structures.

The suite is extended by several sister projects, each providing unique
functionality:

.. list-table:: Extended Functionality
  :widths: 50 150
  :header-rows: 1

  * - Project
    - Description
  * - **docp-core**
    - Centralised core objects, functionality and settings.
  * - **docp-parsers**
    - Parse binary documents (e.g. PDF, PPTX, etc.) into Python objects.
  * - **docp-loaders**
    - Load a parsed document's embeddings into a Chroma vector database, for RAG-enabled LLM use.
  * - **docp-docling**
    - Convert a PDF into Markdown format via wrappers to the ``docling`` libraries.
  * - **docp-dbi**
    - Interfaces to document databases such as ChromaDB, and Neo4j (coming soon).

Installation
============
To install ``docp-core``, first activate your target virtual environment,
then use ``pip``::

    pip install docp-core

For older releases, visit `PyPI`_ or the `GitHub Releases`_ page.

Using the Library
=================
This documentation provides detailed explanations and usage examples for
each importable module. For in-depth documentation, code examples, and
source links, refer to the :ref:`library-api` page.

A **search** field is available in the left navigation bar to help you
quickly locate specific modules or methods.

Troubleshooting
===============
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions,
please :ref:`contact us <contact-us>` or open an issue on `GitHub`_.

Documentation Contents
======================
.. toctree::
    :maxdepth: 1

    library
    changelog
    contact

Indices and Tables
==================
* :ref:`genindex`
* :ref:`modindex`

.. _GitHub Releases: https://github.com/s3dev/docp-core/releases
.. _GitHub: https://github.com/s3dev/docp-core
.. _PyPI: https://pypi.org/project/docp-core/#history

|lastupdated|

