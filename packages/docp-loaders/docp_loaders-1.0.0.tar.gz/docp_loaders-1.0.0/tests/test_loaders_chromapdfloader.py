#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``loaders.chromapdfloader`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import contextlib
import io
import os
from docp_dbi import ChromaDB
from utils4.crypto import crypto
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_loaders import ChromaPDFLoader


class TestChromaPDFLoader(TestBase):
    """Testing class used to test the ``loaders.chromapdfloader`` module."""

    _PATH = '/var/devmt/chroma/docp-loaders'
    _COLLECTION = 'docp-loaders-test-pdf'
    _EMBEDDING_MODEL = '/var/devmt/models/sentence-transformers/all-MiniLM-L6-v2/'
    _OFFLINE = True
    _DBO = ChromaDB(path=_PATH,
                    collection=_COLLECTION,
                    embedding_model_path=_EMBEDDING_MODEL,
                    offline=_OFFLINE)

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='loaders.chromapdfloader')

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the end of all test cases."""
        print(f'Deleting collection: {cls._COLLECTION}')
        cls._DBO.delete_collection()

    def test01a__load__single(self):
        """Test the ``load`` method for a single file.

        :Test:
            - Load a simple PDF into the test collection and verify the
              results.
            - Verify the number of records is as expected.
            - Verify the concatenated document text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        l = ChromaPDFLoader(path=self._DBO,
                            split_text=True,
                            chunk_size=512,
                            chunk_overlap=128)
        l.load(path=path)
        tst = l.chroma.get(where={'source': os.path.basename(path)})
        tst1 = crypto.md5(tst['documents'][0])
        tst2 = crypto.md5(tst['documents'][-1])
        self.assertEqual(7, len(tst['ids']))
        self.assertEqual(os.path.basename(path), tst['metadatas'][0]['source'])
        self.assertEqual('c67cfb5dc11e00c279070ec80ed98e0c', tst1)
        self.assertEqual('a50954653626ea7f4477f7e184259ef3', tst2)

    def test01b__load__multi(self):
        """Test the ``load`` method for multiple files.

        :Test:
            - Load a directory of PDF files into the test collection and
              verify the results.
            - Verify the number of records is as expected.
            - Verify the concatenated document text is as expected.

        """
        l = ChromaPDFLoader(path=self._DBO,
                            split_text=True,
                            chunk_size=512,
                            chunk_overlap=128)
        l.load(path=self._DIR_FILES_PDF_MULTI)
        files = os.listdir(self._DIR_FILES_PDF_MULTI)
        tst = l.chroma.get(where={'source': {'$in': files}})
        tst1 = crypto.md5(''.join(sorted(l.chroma.get(where={'source': files[0]})['documents'])))
        tst2 = crypto.md5(''.join(sorted(l.chroma.get(where={'source': files[1]})['documents'])))
        self.assertEqual(30, len(tst['ids']))
        self.assertIn(tst['metadatas'][0]['source'], files)
        self.assertIn(tst['metadatas'][1]['source'], files)
        self.assertEqual('df2c935b8138705b1d22656804778a0e', tst1)
        self.assertEqual('b1bc7b968dd07acf99e063647315fc16', tst2)

    def test01c__load__from_markdown(self):
        """Test the ``load`` method for a single file loaded from Markdown.

        :Test:
            - Load a simple PDF into the test collection and verify the
              results.
            - Verify the number of records is as expected.
            - Verify the concatenated document text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-header-footer.pdf')
        l = ChromaPDFLoader(path=self._DBO,
                            split_text=True,
                            chunk_size=512,
                            chunk_overlap=128)
        l.load(path=path,
               load_from_markdown=True)  # <-- Added
        tst = l.chroma.get(where={'source': os.path.basename(path)})
        tst1 = crypto.md5(''.join(tst['documents']))
        self.assertEqual(4, len(tst['ids']))
        self.assertEqual('41e3f3cb233adf40b07fb534e67fdc9e', tst1)

    def test01d__load__single_duplicate(self):
        """Test the ``load`` method for a (duplicated) single file.

        :Test:
            - Verify the expected error message is displayed when loading
              a duplicate file.

        """
        buff = io.StringIO()
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        l = ChromaPDFLoader(path=self._DBO,
                            split_text=True,
                            chunk_size=512,
                            chunk_overlap=128)
        with contextlib.redirect_stdout(buff):
            l.load(path=path)
            tst = buff.getvalue()
        self.assertIn('File already loaded', tst)
        self.assertIn('skipping', tst)

    def test01e__load__single_duplicate_allowed_from_markdown(self):
        """Test the ``load`` method for an allowed duplicated file.

        :Test:
            - Load an already loaded PDF file; this time being loaded
              from Markdown.
            - Ensure a duplication warning is not displayed.
            - Verify the number of records is as expected.
            - Verify the concatenated document text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        l = ChromaPDFLoader(path=self._DBO,
                            split_text=True,
                            chunk_size=512,
                            chunk_overlap=128,
                            allow_duplication=True)  # <-- Added
        l.load(path=path, load_from_markdown=True)
        tst = l.chroma.get(where={'$and': [{'pageno': {'$eq': 0}},
                                           {'source': os.path.basename(path)}]})
        tst1 = crypto.md5((''.join(tst['documents'])))
        self.assertEqual(8, len(tst['ids']))
        self.assertEqual('bef7cf8a9f8ec56faa3c3080958d59d4', tst1)

    def test01f__load__single_duplicate_allowed(self):
        """Test the ``load`` method for an allowed duplicated file.

        :Test:
            - Verify no new documents were added due to duplication.
            - Verify processing ended in failure.

        """
        buff = io.StringIO()
        with contextlib.redirect_stdout(buff):
            path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
            l = ChromaPDFLoader(path=self._DBO,
                                split_text=True,
                                chunk_size=512,
                                chunk_overlap=128,
                                allow_duplication=True)  # <-- Added
            l.load(path=path, load_from_markdown=False)  # <-- Duplicate PDF added
            tst = buff.getvalue()
        self.assertIn('No new documents added.', tst)
        self.assertIn('Processing aborted', tst)
        self.assertIn('Failure.', tst)

    def test02a__new_loader__offline_no_embedding(self):
        """Test a new offline loader instance where emb is not provided.

        :Test:
            - Verify an ValueError is raised for an offline loader where
              and embedding model is not provided.

        """
        with contextlib.redirect_stdout(None):
            with self.assertRaises(ValueError):
                ChromaPDFLoader(path=self._PATH,
                                collection=self._COLLECTION,
                                # embedding_model_path=self._EMBEDDING_MODEL  < -- Removed
                                offline=True)
