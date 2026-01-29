#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the superclass which is to be inherited
            by the test-specific modules.

:Platform:  Linux/Windows | Python 3.6+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Reminder:  The testing suite must **not** be deployed into production
            as it contains sensitive information for the development
            environment.

:Example:
    Example code use::

        # Run all tests via the shell script.
        ./run.sh

        # Run all tests using unittest.
        python -m unittest discover

        # Run a single test.
        python -m unittest test_search.py

"""
# pylint: disable=import-error
# pylint: disable=wrong-import-position

import os
import pickle
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import unittest
import warnings
from utils4.crypto import crypto
# locals
from docp_dbi.databases.chroma import ChromaDB
from docp_parsers import PDFParser


class TestBase(unittest.TestCase):
    """Private generalised base-testing class.

    This class is designed to be inherited by each test-specific class.

    """

    _DIR_ROOT = os.path.realpath(os.path.dirname(__file__))
    _DIR_RESC = os.path.join(_DIR_ROOT, 'resources')
    _DIR_CHROMA = os.path.join(_DIR_RESC, 'chroma')
    _DIR_DATA = os.path.join(_DIR_RESC, 'data')
    _DIR_FILES = os.path.join(_DIR_RESC, 'files')
    _DIR_FILES_PDF = os.path.join(_DIR_FILES, 'pdf')
    _DIR_FILES_PPTX = os.path.join(_DIR_FILES, 'pptx')
    _DIR_EMBEDDING_MODEL = ''  # Populated by the child class.
    _COLLECTION = 'unittest'

    @classmethod
    def setUpClass(cls):
        """Setup the testing class once, for all tests."""

    @classmethod
    def tearDownClass(cls):
        """Teardown the testing class once all tests are complete."""

    @classmethod
    def embedding_model_exists(cls) -> bool:
        """Verify the path to the test embedding model exists.

        Returns:
            bool: True if the path exists, otherwise False.

        """
        if not cls._DIR_EMBEDDING_MODEL:
            print('The path to the embedding model (_DIR_EMBEDDING_MODEL) must be set. '
                  'Skipping all tests.')
            return False
        if not os.path.exists(cls._DIR_EMBEDDING_MODEL):
            print('The path to the embedding model cannot be found, skipping all tests.',
                  f'-- {cls._DIR_EMBEDDING_MODEL}',
                  sep='\n')
            return False
        return True

    @staticmethod
    def get_checksum(path: str) -> str:
        """Calculate the MD5 checksum for a given file.

        Args:
            path (str): Full path to the file to be checksummed.

        Returns:
            str: A string containing the MD5 checksum for the given file.

        """
        return crypto.checksum_md5(path=path)

    @classmethod
    def ignore_warnings(cls):
        """Ignore (spurious) warnings for methods under test."""
        warnings.simplefilter(action='ignore', category=ResourceWarning)
        warnings.simplefilter(action='ignore', category=DeprecationWarning)

    @classmethod
    def parse_and_load(cls) -> bool:
        """Parse and load a PDF file into the database for testing.

        Returns:
            bool: True if the load was successful (i.e. the number of
            documents loaded is equal to the number of pages), otherwise
            False.

        """
        pdf = PDFParser(path=os.path.join(cls._DIR_FILES_PDF,
                                          'lorem-ipsum-2-tagged-header-footer.pdf'))
        pdf.extract_text()
        db = ChromaDB(path=cls._DIR_CHROMA,
                      collection=cls._COLLECTION,
                      embedding_model_path=cls._DIR_EMBEDDING_MODEL,
                      offline=True)
        count_a = len(db.get(include=None)['ids'])
        db.add_documents(documents=pdf.doc.documents)
        count_b = len(db.get(include=None)['ids'])
        # Cover the code path where only a single document is passed.
        # This will silently trigger a duplicate in the database, so the
        # counts will still be accurate.
        db.add_documents(documents=pdf.doc.documents[0])
        return (count_b - count_a - pdf.doc.npages) == 0

    def read_pickle(self, module: str, method: str) -> object:
        """Read the named pickle file.

        Args:
            module (str): Name of the module (as this is the path).
            method (str): Name of the caller method (as this is the filename).

        Returns:
            object: An object containing the contents of the serialised
            file.

        """
        path = os.path.join(self._DIR_DATA, module, f'{method}.p')
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data

    @classmethod
    def delete_database(cls):
        """Delete the database collection."""
        db = ChromaDB(path=cls._DIR_CHROMA,
                      collection=cls._COLLECTION,
                      embedding_model_path=cls._DIR_EMBEDDING_MODEL,
                      offline=True)
        db.delete_collection()

    @classmethod
    def reset_warnings(cls):
        """Reset warnings which have been ignored."""
        warnings.resetwarnings()
