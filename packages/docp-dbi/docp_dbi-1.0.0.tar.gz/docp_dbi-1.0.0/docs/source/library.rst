
.. _library-api:

=========================
Library API Documentation
=========================
The page contains simple library usage examples and the module-level
documentation for each of the importable modules in ``docp-dbi``.

.. contents::
    :local:
    :depth: 1

Use Cases
=========
To save digging through the documentation for each module and cobbling 
together what a 'standard use case' may look like, a couple have been
provided here.

Create a ChromaDB interface
---------------------------

.. code-block:: python

    >>> from docp_dbi import ChromaDB

    >>> db = ChromaDB(path='/path/to/chromadb', collection='test-collection')

    # Display a list of all collections in the database.
    >>> db.client.list_collections()

    # Debug: Retrieve records from the database.
    >>> records = db.show_all()


Load a new PDF document into ChromaDB
-------------------------------------

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


Module Documentation
====================
In addition to the module-level documentation, most of the public 
classes and/or methods come with one or more usage examples and access
to the source code itself.

There are two type of modules listed here:

    - Those whose API is designed to be accessed by the user/caller
    - Those which are designated 'private' and designed only for internal
      use

We've exposed both here for completeness and to aid in understanding how
the library is implemented:

.. toctree:: 
   :maxdepth: 1

   databases_chroma

   
|lastupdated|

