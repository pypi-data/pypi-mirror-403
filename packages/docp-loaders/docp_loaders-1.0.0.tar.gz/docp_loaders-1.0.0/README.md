# A basic document parsing and loading utility - Loaders

[![PyPI - Version](https://img.shields.io/pypi/v/docp-loaders?style=flat-square)](https://pypi.org/project/docp-loaders)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/docp-loaders?style=flat-square)](https://pypi.org/project/docp-loaders)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/docp-loaders?style=flat-square)](https://pypi.org/project/docp-loaders)
[![PyPI - Status](https://img.shields.io/pypi/status/docp-loaders?style=flat-square)](https://pypi.org/project/docp-loaders)
[![Static Badge](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](https://pypi.org/project/docp-loaders)
[![Static Badge](https://img.shields.io/badge/code_coverage-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-loaders)
[![Static Badge](https://img.shields.io/badge/pylint_analysis-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-loaders)
[![Documentation Status](https://readthedocs.org/projects/docp-loaders/badge/?version=latest&style=flat-square)](https://docp-loaders.readthedocs.io/en/latest/)
[![PyPI - License](https://img.shields.io/pypi/l/docp-loaders?style=flat-square)](https://opensource.org/license/gpl-3-0)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/docp-loaders?style=flat-square)](https://pypi.org/project/docp-loaders)

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

### The Toolset (Loaders)
As of this release, loaders for the following binary document types are supported:

- PDF
- MS PowerPoint (PPTX)
- (more coming soon)

## Quickstart

### Installation
To install `docp-loaders`, first activate your target virtual environment, then use `pip`:

```bash
pip install docp-loaders
```

For older releases, visit [PyPI][pypi-history] or the [GitHub Releases][github-releases] page.

### Example Usage
For convenience, here are a couple examples for how to parse and load the supported document types into a ChromaDB vector database.

**Parse and load a *single* PDF file into a Chroma database collection:**
```python
>>> from docp_loaders import ChromaPDFLoader

>>> l = ChromaPDFLoader(path='/path/to/chroma',
                        collection='spam')
>>> l.load(path='/path/to/directory/myfile.pdf')
```

**Parse and load a *directory* of PDF files into a Chroma database collection:**
```python
>>> from docp_loaders import ChromaPDFLoader

>>> l = ChromaPDFLoader(path='/path/to/chroma',
                        collection='spam')
>>> l.load(path='/path/to/directory', ext='pdf')
```

**Parse and load a *single* PDF file into a Chroma database collection, offline using a local embedding model:**
```python
>>> from docp_loaders import ChromaPDFLoader

>>> l = ChromaPDFLoader(path='/path/to/chroma',
                        collection='spam',
                        offline=True,
                        embedding_model_path='/path/to/embedding-model-repo')
>>> l.load(path='/path/to/directory/myfile.pdf')
```

**Parse and load a *single* PPTX file into a Chroma database collection:**
```python
>>> from docp_loaders import ChromaPPTXLoader

>>> l = ChromaPPTXLoader(path='/path/to/chroma',
                         collection='spam',
                         split_text=False)
>>> l.load(path='/path/to/directory/myfile.pptx')
```

**Parse and load a *directory* of PPTX files into a Chroma database collection:**
```python
>>> from docp_loaders import ChromaPPTXLoader

>>> l = ChromaPPTXLoader(path='/path/to/chroma',
                         collection='spam',
                         split_text=False)
>>> l.load(path='/path/to/directory', ext='pptx')
```

## Using the Library
The documentation suite provides detailed explanations and usage examples for each importable module. For in-depth documentation, code examples, and source links, refer to the [Library API][api] page.

A **search** field is available in the left navigation bar to help you quickly locate specific modules or methods.

## Troubleshooting
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions, please open an issue on [GitHub][github].

[api]: https://docp-loaders.readthedocs.io/en/latest/
[github]: https://github.com/s3dev/docp-loaders
[github-releases]: https://github.com/s3dev/docp-loaders/releases
[pypi-history]: https://pypi.org/project/docp-loaders/#history
