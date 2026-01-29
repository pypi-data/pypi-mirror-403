#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides a the custom embedding functions which
            enable a user to define the embedding function used for
            ChromaDB's embedding.

            .. important::

                This module should *not* be interacted with directly.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=wrong-import-order

from __future__ import annotations

import chromadb
import os
import torch
from sentence_transformers import SentenceTransformer

# Module based constants:
MODEL_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                           '.cache')


class CustomEmbeddingFunction(chromadb.EmbeddingFunction):
    """Enable user to specify the embedding model to be used.

    Args:
        embedding_model_path (str): Full path to the embedding model to
            be used. Note: This *must* be a valid repo path, as GGUF
            files are currently not supported by the
            ``SentenceTransformer`` class.
        local_files_only (bool): Whether or not to only look at local
            files (i.e., do not try to download the model). This is
            passed directly into the ``SentenceTransformer`` class.


    """

    # Note: Installing torch is a huge overhead, just for this. However, torch
    # will already be installed as part of the sentence-transformers library,
    # so we'll use it here too.
    _MODEL_KWARGS = {'device': 'cuda' if torch.cuda.is_available() else 'cpu',
                     'trust_remote_code': True}

    def __init__(self, embedding_model_path: str, local_files_only: bool):
        """Custom embedding function class initialiser."""
        self._path = embedding_model_path
        self._model = SentenceTransformer(self._path,
                                          cache_folder=MODEL_CACHE,
                                          local_files_only=local_files_only,
                                          **self._MODEL_KWARGS)

    def __call__(self, input: Document) -> Embeddings:  # nocover  # noqa  # pylint: disable=undefined-variable
        """Required call method for a custom embedding function."""
        # pylint: disable=redefined-builtin  # Required by EmbeddingFunction
        return self.embed_documents(input=input)

    @property
    def model(self):
        """Accessor to the internal embedding model."""
        return self._model

    @property
    def model_path(self) -> str:
        """Accessor to the requested model path."""
        return self._path

    def embed_documents(self, input: Document) -> Embeddings:  # noqa  # pylint: disable=undefined-variable
        """Create document embeddings.

        This method is called by the :mod:`langchain_chroma.vectorstores`
        module when loading documents into the database.

        """
        # pylint: disable=redefined-builtin  # Required by EmbeddingFunction
        return self._model.encode(sentences=input, device=self._MODEL_KWARGS.get('device'))
