#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides a localised wrapper and specialised
            functionality around the :class:`langchain_chroma.Chroma`
            class, for interacting with a ChromaDB database.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  This module uses the :class:`langchain_chroma.Chroma`
            class, rather than the base ``chromadb`` library  as
            langchain's implementation provides the ``add_texts`` method
            which supports **GPU processing** and parallelisation. This
            functionality is implemented and accessed through the
            :meth:`~ChromaDB.add_documents` method.

"""
# pylint: disable=wrong-import-order

from __future__ import annotations

import chromadb
import os
from hashlib import md5
# langchain's Chroma is used rather than the base chromadb as it provides
# the add_texts method which support GPU processing and parallelisation.
from langchain_chroma import Chroma as _LangChroma
# locals
try:
    from ._embeddingfunctions import CustomEmbeddingFunction
except ImportError:
    from docp_dbi.databases._embeddingfunctions import CustomEmbeddingFunction


class ChromaDB(_LangChroma):
    r"""Wrapper class around the ``chromadb`` library.

    Args:
        path (str): Path to the chromadb database's *directory*.
        collection (str): Collection name.
        embedding_model_path (str, optional): Path to a *local* embedding
            model *repo* of your choosing. Defaults to None.
            If not provided, the ``SentenceTransformers`` class be be
            allowed free reign to download or use the model named in the
            :attr:`DEFAULT_EMBEDDING_MODEL` attribute.
        repo_id (str, optional): HuggingFace repository ID for the
            requested embedding model. Defaults to None.
        offline (bool, optional): Remain offline. Use the local model
            embedding function model repo rather than obtaining one
            online. Defaults to False.

    :Examples:

        Load a new PDF document into ChromaDB::

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
            ...               embedding_model_path=('/path/to/models/sentence-transformers/'
                                                    'all-MiniLM-L6-v2'),
            ...               offline=True)
            # Embed and store the document chunks.
            >>> db.add_documents(documents=docs)

            # Run your first query.
            >>> result = db.collection.query(query_texts=['How do I implement a RAG pipeline?'])

    """

    # TODO: Move this to a config file in docp-core.
    DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

    def __init__(self,
                 path: str,
                 collection: str,
                 *,
                 embedding_model_path: str=None,
                 repo_id: str=None,
                 offline: bool=False):
        """Chroma database class initialiser."""
        self._path = os.path.realpath(path)
        self._cname = collection
        self._embpath = embedding_model_path
        self._repo_id = repo_id
        self._offline = offline
        self._oclient = None         # Database 'client' object
        self._ocollection = None     # Database 'collection' object.
        self._set_client()
        self._set_embedding_fn()
        self._set_collection()
        super().__init__(client=self._oclient,
                         collection_name=self._cname,
                         embedding_function=self._embfn,
                         persist_directory=self._path)

    def __repr__(self) -> str:
        """Define the information about this class to be displayed."""
        metric = self.collection.__dict__['_model']['configuration_json']['hnsw']['space']
        return (f'<class: {self.__class__.__name__}>\n'
                f'Collection: {self.collection.name}\n'
                f'Similarity metric: {metric}\n'
                f'Embedding function: {self.embedding_function.model}\n'
                f'Embedding model path: {self.embedding_function.model_path}')

    @property
    def client(self) -> chromadb.api.client.Client:  # nocover
        """Accessor to the :class:`chromadb.PersistentClient` class."""
        return self._oclient

    @property
    def collection(self) -> chromadb.api.models.Collection.Collection:  # nocover
        """Accessor to the chromadb client's collection object."""
        return self._ocollection

    @property
    def embedding_function(self) -> CustomEmbeddingFunction:
        """Accessor to the embedding function used."""
        return self._embfn

    @property
    def path(self) -> str:
        """Accessor to the database's path."""
        return self._path

    def add_documents(self, documents: list[Document]) -> None:  # noqa  # pylint: disable=undefined-variable
        """Add multiple documents to the collection.

        This method overrides the base class' ``add_documents`` method
        to enable local ID derivation. Knowing *how* the IDs are derived
        gives us greater understanding and querying ability of the
        documents in the database. Each ID is derived locally by the
        :meth:`_preproc` method from the file's basename, page number
        and page content.

        Additionally, this method wraps the
        :func:`langchain_chroma.Chroma.add_texts` method which supports
        GPU processing and parallelisation.

        Args:
            documents (list[Document]): A list of :class:`Document`
                objects. These objects can be of either type:

                    - :class:`langchain_core.documents.Document`
                    - :class:`docp_core.objects.documentobject.Document`

        """
        # pylint: disable=arguments-differ
        if not isinstance(documents, list):
            documents = [documents]
        ids_, docs_, meta_ = self._preproc(docs=documents)
        self.add_texts(ids=ids_, texts=docs_, metadatas=meta_)

    def show_all(self, include: list[str]=None) -> dict:
        """Return the entire contents of the collection.

        This is an alias around ``.collection.get()``.

        Args:
            include (list[str], optional): A list of what to include in
                the results. Can contain `"embeddings"`, `"metadatas"`,
                `"documents"`. IDs are always included.
                Defaults to `["metadatas", "documents"]`.

        """
        include = include or ['metadatas', 'documents']
        return self._ocollection.get(include=include)

    def _get_embedding_function_model(self) -> str:
        """Derive the path to the embedding function model.

        .. note::
            If the user has specified a *local* embedding model path,
            and that path exists, this model path is returned.

            If the user provides a repository ID, this ID is passed into
            the :class:`SentenceTransformer` class to handle as
            appropriate, via the :class:`CustomEmbeddingFunction`. class

            If the user does not provide either an embedding model path,
            nor a repository ID, the default embedding model value is
            used.

        Raises:
            FileNotFoundError: If the requested embedding model path does
            not exist.

        Returns:
            str: The path to the local embedding model, the model
            repository ID or the default embedding model ID.

        """
        # User has specified the path to the local model they want to use.
        if self._embpath:
            if os.path.exists(self._embpath):
                return self._embpath
            raise FileNotFoundError('The requested model path cannot be found:\n'
                                    f'-- {self._embpath}')
        # User has specified repo_id *only*. Lets SentenceTransformer decide how to handle.
        if self._repo_id and self._embpath is None:  # nocover  # N/A in testing env.
            return self._repo_id
        # User has *not* specified an embedding model path, nor a repo ID.
        return self.DEFAULT_EMBEDDING_MODEL  # nocover  # N/A in testing env.

    @staticmethod
    def _preproc(docs: list[Document]) -> tuple:  # noqa  # pylint: disable=undefined-variable
        """Pre-process the document objects to create the IDs.

        Parse the ``Document`` object into its parts for storage.
        Additionally, create the ID as a hash of the source document's
        basename, page number and content.

        Args:
            docs (list[Document]): A list of Document objects which are
                used to derive the database ID, and split into the
                return values.

        Returns:
            tuple: A tuple containing:

                - ([ids], [texts], [metadatas])

            These values are passed into the :meth:`~add_texts` method
            for embedding and storage.

        """
        ids = []
        txts = []
        metas = []
        for doc in docs:
            pc = doc.page_content
            m = doc.metadata
            pc_, src_ = map(str.encode, (pc, m['source']))
            pg_ = str(m.get('pageno', 0)).zfill(4)
            id_ = f'id_{md5(src_).hexdigest()}_{pg_}_{md5(pc_).hexdigest()}'
            ids.append(id_)
            txts.append(pc)
            metas.append(m)
        return ids, txts, metas

    def _set_client(self) -> None:
        """Set the database client object.

        :Note:
            ChromaDB telemetry has been disabled.

        """
        # pylint: disable=no-member  # Settings, PersistentClient
        settings = chromadb.Settings(anonymized_telemetry=False)
        self._oclient = chromadb.PersistentClient(path=self._path, settings=settings)

    def _set_collection(self) -> None:
        """Set the database collection object.

        If the collection does not already exist, it is created using
        *cosine* as a similarity metric.

        """
        self._ocollection = self._oclient.get_or_create_collection(self._cname,
                                                                   metadata={'hnsw:space':
                                                                             'cosine'},
                                                                   embedding_function=self._embfn)

    def _set_embedding_fn(self) -> None:
        """Set the embeddings function object."""
        path = self._get_embedding_function_model()
        self._embfn = CustomEmbeddingFunction(embedding_model_path=path,
                                              local_files_only=self._offline)
