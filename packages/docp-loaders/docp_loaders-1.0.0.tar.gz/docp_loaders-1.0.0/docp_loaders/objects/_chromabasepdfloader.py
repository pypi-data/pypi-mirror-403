#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the mid-level functionality to parse
            and store PDF files into a Chroma vector database.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

.. attention::

            This module is *not* designed to be interacted with
            directly, only via the appropriate interface class(es).

            Rather, please create an instance of a Chroma PDF document
            loading object using the following class:

                - :class:`~docp_loaders.loaders.chromapdfloader.ChromaPDFLoader`

"""

import inspect
from docp_docling import PDFParser as PDFParser_d  # For PDF to Markdown conversion.
from docp_parsers import PDFParser as PDFParser_p  # For PDF extraction.
from utils4.user_interface import ui
# locals
try:
    from ..objects._chromabaseloader import _ChromaBaseLoader
except ImportError:
    from docp_loaders.objects._chromabaseloader import _ChromaBaseLoader


class _ChromaBasePDFLoader(_ChromaBaseLoader):
    """Base class for loading PDF documents into a Chroma vector database.

    This class is a specialised version of the
    :class:`~docp.loaders._chromabaseloader._ChromaBaseLoader` class,
    designed to handle PDF presentations.

    """
    # pylint: disable=attribute-defined-outside-init  # These are defined in the base class.

    #
    # No __init__ method here to ensure the ultimate base class'
    # signature is used and to save passing loads of stuff around, if we
    # don't have to.
    #

    def _parse_text(self, **kwargs) -> bool:
        """Parse text from the document.

        :Keyword Arguments:
            Those to be passed into the text extraction method.

        Returns:
            bool: True if the parser's 'text' object is populated,
            otherwise False.

        """
        print('- Extracting text ...')
        if self._from_md:
            self._parse_text_md(**kwargs)
        else:
            self._parse_text_pdf(**kwargs)
        if len(self._p.doc.documents) == 0:  # nocover
            ui.print_warning(f'No text extracted from {self._p.doc.basename}')
            return False
        return True

    def _parse_text_md(self, **kwargs):
        """Parse text from the document.

        :Keyword Arguments:
            Those to be passed into the text extraction method.

        """
        # Filter kwargs to only those accepted by the target function.
        args = set(inspect.signature(self._p.to_markdown).parameters.keys())
        kwargs = {k: v for k, v in kwargs.items() if k in args}
        self._p.to_markdown(**kwargs)

    def _parse_text_pdf(self, **kwargs):
        """Parse text from the document.

        :Keyword Arguments:
            Those to be passed into the text extraction method.

        """
        # Filter kwargs to only those accepted by the target function.
        args = set(inspect.signature(self._p.extract_text).parameters.keys())
        kwargs = {k: v for k, v in kwargs.items() if k in args}
        self._p.extract_text(**kwargs)

    def _set_parser(self):
        """Set the appropriate document parser.

        Setting the parser creates a parser instance as an attribute of
        this class. When the parser instance is created, various file
        verification checks are made. For detail, refer to the following
        parsers classes:

            - :class:`docp_docling.parsers.pdfparser.PDFParser`
            - :class:`docp_parsers.parsers.pdfparser.PDFParser`

        """
        if self._from_md:
            self._p = PDFParser_d(path=self._fpath, detailed_extraction=False)
        else:
            self._p = PDFParser_p(path=self._fpath)
