==================================
docp-loaders Library Documentation
==================================

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

Toolset (docp-loaders)
----------------------
As of this release, loaders for the following binary document types are
supported:

- PDF
- MS PowerPoint (PPTX)
- more coming soon ...


Quickstart
==========

Installation
------------
To install ``docp-loaders``, first activate your target virtual environment,
then use ``pip``::

    pip install docp-loaders

For older releases, visit `PyPI`_ or the `GitHub Releases`_ page.


Example Usage
-------------
For convenience, here are a couple examples for how to parse and load the
supported document types into a ChromaDB vector database.

**Parse and load a *single* PDF file into a Chroma database collection:**

.. code-block:: python

    >>> from docp_loaders import ChromaPDFLoader

    >>> l = ChromaPDFLoader(path='/path/to/chroma',
                            collection='spam')
    >>> l.load(path='/path/to/directory/myfile.pdf')


**Parse and load a *directory* of PDF files into a Chroma database collection:**

.. code-block:: python

    >>> from docp_loaders import ChromaPDFLoader

    >>> l = ChromaPDFLoader(path='/path/to/chroma',
                            collection='spam')
    >>> l.load(path='/path/to/directory', ext='pdf')


**Parse and load a *single* PDF file into a Chroma database collection, offline using a local embedding model:**

.. code-block:: python

    >>> from docp_loaders import ChromaPDFLoader

    >>> l = ChromaPDFLoader(path='/path/to/chroma',
                            collection='spam',
                            offline=True,
                            embedding_model_path='/path/to/embedding-model-repo')
    >>> l.load(path='/path/to/directory/myfile.pdf')


**Parse and load a *single* PPTX file into a Chroma database collection:**

.. code-block:: python

    >>> from docp_loaders import ChromaPPTXLoader

    >>> l = ChromaPPTXLoader(path='/path/to/chroma',
                             collection='spam',
                             split_text=False)
    >>> l.load(path='/path/to/directory/myfile.pptx')


**Parse and load a *directory* of PPTX files into a Chroma database collection:**

.. code-block:: python

    >>> from docp_loaders import ChromaPPTXLoader

    >>> l = ChromaPPTXLoader(path='/path/to/chroma',
                             collection='spam',
                             split_text=False)
    >>> l.load(path='/path/to/directory', ext='pptx')


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

.. _GitHub Releases: https://github.com/s3dev/docp-loaders/releases
.. _GitHub: https://github.com/s3dev/docp-loaders
.. _PyPI: https://pypi.org/project/docp-loaders/#history

|lastupdated|

