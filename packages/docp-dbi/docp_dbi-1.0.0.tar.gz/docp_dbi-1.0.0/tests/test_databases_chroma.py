#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``databases.chroma`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import unittest
from utils4.crypto import crypto
# locals
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_dbi.databases.chroma import ChromaDB


class TestChromaDB(TestBase):
    """Testing class used to test the ``databases.chroma`` module."""

    _DIR_EMBEDDING_MODEL = '/var/devmt/models/sentence-transformers/all-MiniLM-L6-v2/'

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases.

        At the start of testing, the testing ChromaDB database collection
        is reset, the loaded with a testing PDF file.

        """
        testutils.msgs.startoftest(msg='databases.chroma')
        cls.ignore_warnings()
        if not cls.embedding_model_exists():
            raise unittest.SkipTest('Embedding model not available.')
        cls.delete_database()
        if not cls.parse_and_load():
            raise unittest.SkipTest('Parse and load attempt filed.')

    @classmethod
    def tearDownClass(cls):
        """Actions to be performed after all tests are complete."""
        cls.delete_database()
        cls.reset_warnings()

    def test01a__black_box(self):
        """Test the PDF load as a black box.

        :Test:
            - Verify the PDF document text was loaded as expected.

        """
        db = self._create_db_instance()
        data = db.show_all(include=['documents'])
        exp_pg1 = 'eac8dd0155ecce0320e1a0285ad5e240'
        exp_pg2 = 'c2a69b064156a25dd006e0ba3604a17b'
        tst_pg1 = crypto.md5(data['documents'][0])
        tst_pg2 = crypto.md5(data['documents'][1])
        self.assertEqual(exp_pg1, tst_pg1)
        self.assertEqual(exp_pg2, tst_pg2)

    def test02a__id_derivation(self):
        """Test the IDs for the loaded PDF file.

        :Test:
            - Verify the derived IDs match the expected values.

        """
        db = self._create_db_instance()
        data = db.show_all(include=['documents', 'metadatas'])
        source_hash = crypto.md5(data['metadatas'][0]['source'])
        for i in range(2):
            with self.subTest(msg=f'Page {i+1}'):
                content_hash = crypto.md5(data['documents'][i])
                pageno = data['metadatas'][i]['pageno']
                tst = f'id_{source_hash}_{pageno:04d}_{content_hash}'
                exp = data['ids'][i]
                self.assertEqual(exp, tst)

    def test03a__repr(self):
        """Test the repr/str display to the terminal.

        :Test:
            - Verify the display to stdout contains the expected values.

        """
        db = self._create_db_instance()
        exp1 = f'class: {db.__class__.__name__}'
        exp2 = f'Collection: {self._COLLECTION}'
        exp3 = 'Similarity metric: cosine'
        exp4 = 'SentenceTransformer'
        exp5 = f'Embedding model path: {self._DIR_EMBEDDING_MODEL}'
        tst = repr(db)
        self.assertIn(exp1, tst)
        self.assertIn(exp2, tst)
        self.assertIn(exp3, tst)
        self.assertIn(exp4, tst)
        self.assertIn(exp5, tst)

    def test04a__path(self):
        """Test the ``path`` attribute.

        :Test:
            - Verify the expected value is returned.

        """
        db = self._create_db_instance()
        exp = self._DIR_CHROMA
        tst = db.path
        self.assertIn(exp, tst)

    def test05a__show_all(self):
        """Test the ``show_all`` attribute.

        :Test:
            - Verify the returned keys match the ``include`` argument.

        """
        db = self._create_db_instance()
        include = ['metadatas', 'embeddings']
        tst = db.show_all(include=include)
        ids = tst['ids']
        emb = tst['embeddings']
        doc = tst['documents']
        uri = tst['uris']
        inc = tst['included']
        dat = tst['data']
        met = tst['metadatas']
        self.assertEqual(2, len(ids))
        self.assertEqual(2, len(emb))
        self.assertIsNone(doc)
        self.assertIsNone(uri)
        self.assertEqual(include, inc)
        self.assertIsNone(dat)
        self.assertEqual(2, len(met))

    def test06a___get_embedding_function_model(self):
        """Test the ``_get_embedding_function_model`` attribute.

        :Test:
            - Verify a non-existant path raises a FileNotFoundError.

        """
        with self.assertRaises(FileNotFoundError):
            ChromaDB(path=self._DIR_CHROMA,
                     collection=self._COLLECTION,
                     embedding_model_path='/path/no/nowhere',
                     offline=True)

    def _create_db_instance(self) -> ChromaDB:

        """Wrapper method to easily create a test database instance."""
        return ChromaDB(path=self._DIR_CHROMA,
                        collection=self._COLLECTION,
                        embedding_model_path=self._DIR_EMBEDDING_MODEL,
                        offline=True)
