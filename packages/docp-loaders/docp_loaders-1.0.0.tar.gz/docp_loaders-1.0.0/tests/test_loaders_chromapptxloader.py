#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``loaders.chromapptxloader`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

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
from docp_loaders import ChromaPPTXLoader


class TestChromaPPTXLoader(TestBase):
    """Testing class used to test the ``loaders.chromapptxloader`` module."""

    _PATH = '/var/devmt/chroma/docp-loaders'
    _COLLECTION = 'docp-loaders-test-pptx'
    _EMBEDDING_MODEL = '/var/devmt/models/sentence-transformers/all-MiniLM-L6-v2/'
    _OFFLINE = True
    _DBO = ChromaDB(path=_PATH,
                    collection=_COLLECTION,
                    embedding_model_path=_EMBEDDING_MODEL,
                    offline=_OFFLINE)

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='loaders.chromapptxloader')

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
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-lg.pptx')
        l = ChromaPPTXLoader(path=self._DBO, split_text=False)
        l.load(path=path)
        tst = l.chroma.get(where={'source': os.path.basename(path)})
        tst1 = crypto.md5('\n'.join(tst['documents']))
        self.assertEqual(61, len(tst['ids']))
        self.assertEqual(os.path.basename(path), tst['metadatas'][0]['source'])
        self.assertEqual('b793bf3c37f3535c2477c18fc9acfb13', tst1)

    def test01b__load__multi(self):
        """Test the ``load`` method for multiple files.

        :Test:
            - Load a directory of PDF files into the test collection and
              verify the results.
            - Verify the number of records is as expected.
            - Verify the concatenated document text is as expected.

        """
        l = ChromaPPTXLoader(path=self._DBO, split_text=False)
        l.load(path=self._DIR_FILES_PPTX_MULTI)
        files = os.listdir(self._DIR_FILES_PPTX_MULTI)
        tst = l.chroma.get(where={'source': {'$in': files}})
        tst1 = crypto.md5(''.join(sorted(l.chroma.get(where={'source': files[0]})['documents'])))
        tst2 = crypto.md5(''.join(sorted(l.chroma.get(where={'source': files[1]})['documents'])))
        self.assertEqual(52, len(tst['ids']))
        self.assertIn(tst['metadatas'][0]['source'], files)
        self.assertIn(tst['metadatas'][1]['source'], files)
        self.assertEqual('2f85490b0ca8b4ced1b5e26b0f8fa4d0', tst1)
        self.assertEqual('d40627e315be11870c9ad06621ddbbc1', tst2)
