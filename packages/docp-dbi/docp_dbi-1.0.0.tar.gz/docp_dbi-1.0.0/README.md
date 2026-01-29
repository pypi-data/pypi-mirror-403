# A basic document parsing and loading utility - Database Interfaces

[![PyPI - Version](https://img.shields.io/pypi/v/docp-dbi?style=flat-square)](https://pypi.org/project/docp-dbi)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/docp-dbi?style=flat-square)](https://pypi.org/project/docp-dbi)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/docp-dbi?style=flat-square)](https://pypi.org/project/docp-dbi)
[![PyPI - Status](https://img.shields.io/pypi/status/docp-dbi?style=flat-square)](https://pypi.org/project/docp-dbi)
[![Static Badge](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](https://pypi.org/project/docp-dbi)
[![Static Badge](https://img.shields.io/badge/code_coverage-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-dbi)
[![Static Badge](https://img.shields.io/badge/pylint_analysis-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-dbi)
[![Documentation Status](https://readthedocs.org/projects/docp-dbi/badge/?version=latest&style=flat-square)](https://docp-dbi.readthedocs.io/en/latest/)
[![PyPI - License](https://img.shields.io/pypi/l/docp-dbi?style=flat-square)](https://opensource.org/license/gpl-3-0)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/docp-dbi?style=flat-square)](https://pypi.org/project/docp-dbi)

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

This library (``docp-dbi``) extends the document parsing capability by adding access to a ChromaDB vector database for storing text embeddings. This is particularly useful for implementing RAG-enabled pipelines.

### The Toolset (Interfaces)
As of this release, the following database interfaces are supported:

- ChromaDB (via ``langchain_chroma``)
- Neo4j (coming soon)

## Quickstart

### Installation
To install `docp-dbi`, first activate your target virtual environment, then use `pip`:

```bash
pip install docp-dbi
```

For older releases, visit [PyPI][pypi-history] or the [GitHub Releases][github-releases] page.

### Example Usage
For convenience, here are a couple examples for how to create and interact with a database interface for your project.

**Create an interface to ChromaDB:**

``` python
    >>> from docp_dbi import ChromaDB

    # Create a database interface.
    >>> db = ChromaDB(path='/path/to/chromadb', collection='test-collection')

    # Display a list of all collections in the database.
    >>> db.client.list_collections()

    # Debug: Retrieve records from the database.
    >>> records = db.show_all()
```

**Load a new PDF document into the database, and query against it:**

``` python
    >>> from docp_dbi import ChromaDB
    >>> from docp_parsers import PDFParser
    >>> from langchain_text_splitters import RecursiveCharacterTextSplitter

    # Parse the PDF document.
    >>> pdf = PDFParser(path='/path/to/documents/rag-pipelines-how-to.pdf')
    >>> pdf.extract_text()

    # Setup a text splitter (for chunking the document).
    >>> splitter = RecursiveCharacterTextSplitter(
    ...     separators=['\n\n\n', '\n\n', '\n', '.'],
    ...     chunk_size=512,
    ...     chunk_overlap=128
    ... )
    # Split the document for storage.
    >>> docs = splitter.split_documents(pdf.doc.documents)

    # Create a database interface, using an offline, local user-defined embedding model.
    >>> db = ChromaDB(path='/path/to/databases/chroma/', 
    ...               collection='test', 
    ...               embedding_model_path='/path/to/models/sentence-transformers/all-MiniLM-L6-v2', 
    ...               offline=True)
    # Embed and store the document chunks.
    >>> db.add_documents(documents=docs)

    # Run your first query.
    >>> result = db.collection.query(query_texts=['How do I implement a RAG pipeline?'])
```

## Using the Library
The documentation suite provides detailed explanations and usage examples for each importable module. For in-depth documentation, code examples, and source links, refer to the [Library API][api] page.

A **search** field is available in the left navigation bar to help you quickly locate specific modules or methods.

## Troubleshooting
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions, please open an issue on [GitHub][github].

[api]: https://docp-dbi.readthedocs.io/en/latest/
[github]: https://github.com/s3dev/docp-dbi
[github-releases]: https://github.com/s3dev/docp-dbi/releases
[pypi-history]: https://pypi.org/project/docp-dbi/#history

