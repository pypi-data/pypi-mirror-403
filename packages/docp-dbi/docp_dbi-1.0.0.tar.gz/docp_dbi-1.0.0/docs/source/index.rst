==============================
docp-dbi Library Documentation
==============================

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

This library (``docp-dbi``) extends the document parsing capability by 
adding access to a ChromaDB vector database for storing text embeddings.
This is particularly useful for implementing RAG-enabled pipelines.

Toolset (docp-dbi)
------------------
As of this release, the following database interfaces are supported:

- ChromaDB (via ``langchain_chroma``)
- Neo4j (coming soon)

Quickstart
==========

Installation
------------
To install ``docp-dbi``, first activate your target virtual environment,
then use ``pip``::

    pip install docp-dbi

For older releases, visit `PyPI`_ or the `GitHub Releases`_ page.

Example Usage
-------------
For convenience, here are a couple examples for how to create and interact
with a database interface for your project.

Create an interface to ChromaDB:

.. code-block:: python

    >>> from docp_dbi import ChromaDB

    >>> db = ChromaDB(path='/path/to/chromadb', collection='test-collection')

    # Display a list of all collections in the database.
    >>> db.client.list_collections()

    # Debug: Retrieve records from the database.
    >>> records = db.show_all()


Load a new PDF document into the database, and query against it:

.. code-block:: python

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

.. _GitHub Releases: https://github.com/s3dev/docp-dbi/releases
.. _GitHub: https://github.com/s3dev/docp-dbi
.. _PyPI: https://pypi.org/project/docp-dbi/#history

|lastupdated|

