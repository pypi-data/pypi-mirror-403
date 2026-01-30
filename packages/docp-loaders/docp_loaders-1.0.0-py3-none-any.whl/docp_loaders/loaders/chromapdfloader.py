#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the entry point for loading PDF files
            into a Chroma database.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

:Examples:

    Parse and load a *single* PDF file into a Chroma database
    collection::

        >>> from docp_loaders import ChromaPDFLoader

        >>> l = ChromaPDFLoader(path='/path/to/chroma',
                                collection='spam')
        >>> l.load(path='/path/to/directory/myfile.pdf')


    Parse and load a *directory* of PDF files into a Chroma database
    collection::

        >>> from docp_loaders import ChromaPDFLoader

        >>> l = ChromaPDFLoader(path='/path/to/chroma',
                                collection='spam')
        >>> l.load(path='/path/to/directory', ext='pdf')


    For further example code use, please refer to the
    :class:`ChromaPDFLoader` class docstring.

"""

import os
from docp_core.utilities import utilities
# locals
try:
    from ..objects._chromabasepdfloader import _ChromaBasePDFLoader
except ImportError:
    from docp_loaders.objects._chromabasepdfloader import _ChromaBasePDFLoader


class ChromaPDFLoader(_ChromaBasePDFLoader):
    r"""Chroma database PDF-specific document loader.

    Args:
        path (str | ChromaDB): Either the full path to the Chroma
            database *directory*, or an instance of a
            :class:`~docp.dbs.chroma.ChromaDB` class. If the instance is
            passed, the ``collection`` argument is ignored.
        collection (str, optional): Name of the Chroma database
            collection. Only required if the ``dbpath`` parameter is a
            path. Defaults to None.
        split_text (bool, optional): Split the document into chunks,
            before loading it into the database. Defaults to True.
        chunk_size (int, optional): Size (in characters) of each text
            chunk after splitting. Defaults to 512.
        chunk_overlap (int, optional): Number of characters to overlap in
            the split text.  Defaults to 128.
        separators (list, optional): Separators to be used by the
            recursive text splitter.
            Defaults to ``['\n\n\n', '\n\n', '\n', ' ']``.
        separators_md (list, optional): Separators to be used by the
            recursive text splitter, **for Markdown files**.
            Defaults to ``['#', '##', '###', '\n']``.
        embedding_model_path (str, optional): Path to the embedding model
            to be used. Defaults to None.
        repo_id (str, optional): Huggingface repository name to be used
            as the embedding model. Defaults to None.
        offline (bool, optional): Remain offline and use the locally
            cached embedding function model. Defaults to False.

    :Examples:

        Parse and load a *single* PDF file into a Chroma database
        collection::

            >>> from docp_loaders import ChromaPDFLoader

            >>> l = ChromaPDFLoader(path='/path/to/chroma',
                                    collection='spam')
            >>> l.load(path='/path/to/directory/myfile.pdf')


        Parse and load a *directory* of PDF files into a Chroma
        database collection::

            >>> from docp_loaders import ChromaPDFLoader

            >>> l = ChromaPDFLoader(path='/path/to/chroma',
                                    collection='spam')
            >>> l.load(path='/path/to/directory', ext='pdf')

    """

    #
    # No __init__ method here to ensure the ultimate base class'
    # signature is used and to save passing loads of stuff around, if we
    # don't have to.
    #

    def load(self,
             path: str,
             *,
             ext: str='**',
             recursive: bool=True,
             load_from_markdown: bool=False,
             # docp_parsers.PDFParser.extract_text -->
             remove_header: bool=True,
             remove_footer: bool=True,
             remove_newlines: bool=True,
             ignore_tags: set=None,
             convert_to_ascii: bool=True,
             x_tolerance: int=3,
             y_tolerance: int=3,
             # docp_docling.PDFParser.to_markdown -->
             page_no: int=None,
             image_mode: str='placeholder',
             include_annotations: bool=True,
             unique_lines: bool=False,
             **kwargs) -> None:
        """Load a PDF file (or files) into a Chroma database.

        .. note::

            There are *many* argument in this method. This is because
            these arguments are passed into the document parser(s). Any
            argument which is not accepted by the target parser is simply
            ignored.

        Args:
            path (str): Full path to the file (or *directory*) to be
                parsed and loaded. Note: If this is a directory, a
                specific file extension can be passed into the
                :meth:`load` method using the ``ext`` argument.
            ext (str, optional): If the ``path`` argument refers to a
                *directory*, a specific file extension can be specified
                here. For example: ``ext = 'pdf'``. Defaults to '**',
                for a recursive search.

                .. note::

                    If anything other than ``'**'`` is provided, all
                    alpha-characters are parsed from the string, and
                    prefixed with ``*.``. Meaning, if ``'.pdf'`` is
                    passed, the characters ``'pdf'`` are parsed and
                    prefixed with ``*.`` to create ``'*.pdf'``. However,
                    if ``'things.foo'`` is passed, the derived extension
                    will be ``'*.thingsfoo'``.

            recursive (bool, optional): If True, subdirectories are
                searched. Defaults to True.
            load_from_markdown (bool, optional): Convert the PDF text to
                Markdown format and load from the Markdown text.
                Defaults to False.

                .. tip::

                    This is particularly useful when loading PDF
                    documents for use with a RAG pipeline as this method
                    of loading is designed to **keep document sections
                    together** as chunks in the database, which aids in
                    more complete content retrieval.

                    **Note:**
                    This is more processing intensive as ``docling``
                    models are required for the conversion.

            remove_header (bool, optional): Attempt to remove the header
                from each page. Defaults to True.
            remove_footer (bool, optional): Attempt to remove the footer
                from each page. Defaults to True.
            remove_newlines (bool, optional): Replace newline characters
                with a space. Defaults to True, as this helps with
                document chunk splitting.
            ignore_tags (set, optional): If provided, these are the
                PDF 'marked content' tags which will be ignored. Note
                that the PDF document must contain tags, otherwise the
                bounding box method is used and this argument is ignored.
                Defaults to ``{'Artifact'}``, as these generally
                relate to a header and/or footer. To include all tags,
                (not skip any) pass this argument as ``'na'``.
            convert_to_ascii (bool, optional): Convert all characters to
                ASCII. Defaults to True.
            x_tolerance (int, optional): Adds space where the difference
                between x1 of one character and the x0 of the next
                character is greater than x_tolerance. Defaults to 3.
            y_tolerance (int, optional): Adds space where the difference
                between y1 of one character and the y0 of the next
                character is greater than y_tolerance. Defaults to 3.
            page_no (int, optional): Page number to convert.
                Defaults to None (for all pages).
            image_mode (str, optional): The mode to use for including
                images in the markdown. Options are: 'embedded',
                'placeholder', 'referenced'. Defaults to 'placeholder'.
            include_annotations (bool, optional): Whether to include
                annotations in the export. Defaults to True.
            unique_lines (bool, optional): Remove any duplicated lines
                from the document's content. Generally used to remove
                repeated header and footer strings. Defaults to False.

        :Keyword Args:
            kwargs (dict): Additional keywords to be passed into the
            document parser(s).

        """
        # pylint: disable=too-many-locals  # A lot of arguments are needed.
        # Prepare the arguments being sent to the doc parser.
        # - This has been done manually as using locals() introduces
        #   unpredictable behaviour.
        _kwargs = {
                   # docp_parsers.PDFParser.extract_text -->
                   'remove_header': remove_header,
                   'remove_footer': remove_footer,
                   'remove_newlines': remove_newlines,
                   'ignore_tags': ignore_tags,
                   'convert_to_ascii': convert_to_ascii,
                   'x_tolerance': x_tolerance,
                   'y_tolerance': y_tolerance,
                   # docp_docling.PDFParser.to_markdown -->
                   'page_no': page_no,
                   'image_mode': image_mode,
                   'include_annotations': include_annotations,
                   'unique_lines': unique_lines,
                   **kwargs,
                  }
        self._from_md = load_from_markdown  # Set parent class' flag.
        # Load multi
        if os.path.isdir(path):
            files = utilities.collect_files(path=path, ext=ext, recursive=recursive)
            count = len(files)
            for idx, f in enumerate(files, 1):
                print(f'\nProcessing {idx} of {count}: {os.path.basename(f)}')
                self._load(path=f, **_kwargs)
        # Load single
        else:
            print(f'Processing: {os.path.basename(path)} ...')
            self._load(path=path, **_kwargs)
