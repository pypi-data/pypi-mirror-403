#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the base functionality for parsing and
            storing a document's data into a Chroma vector database.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

.. attention::

            This module is *not* designed to be interacted with
            directly, only via the appropriate interface class(es).

            Rather, please create an instance of a Chroma
            document-type-specific loader object using one of the
            following classes:

                - :class:`~docp.loaders.chromapdfloader.ChromaPDFLoader`
                - :class:`~docp.loaders.chromapptxloader.ChromaPPTXLoader`

"""

import os
from chromadb.api.types import errors as chromadberrors
from docp_dbi import ChromaDB
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils4.reporterror import reporterror
from utils4.user_interface import ui


class _ChromaBaseLoader:
    """Base class for loading documents into a Chroma vector database.

    Args:
        path (str | ChromaDB): Either the full path to the Chroma
            database *directory*, or an instance of a
            :class:`~docp_dbi.databases.chroma.ChromaDB` class.
            If the instance is passed, the ``collection`` argument is
            ignored as it's already embedded in the database object.
        collection (str, optional): Name of the Chroma database
            collection. Only required if the ``db`` parameter is a path.
            Defaults to None.
        split_text (bool, optional): Split the document into chunks,
            before loading it into the database. Defaults to True.
        allow_duplication (bool, optional): Disable the check which
            prevents the same document filename from being loaded
            multiple times. Defaults to False.

            .. tip::

                Allowing duplication is useful if the same document
                is to be loaded into the database from multiple formats.
                For example, loading a document from parsed PDF and the
                same PDF, but in Markdown format.

                **Use with care.**

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

    """
    # pylint: disable=assignment-from-no-return  # These are stub methods.

    _PFX_ERR = '\n[ERROR]:'
    _PFX_WARN = '\n[WARNING]:'

    def __init__(self,
                 path: str | ChromaDB,
                 collection: str=None,
                 *,
                 split_text: bool=True,
                 allow_duplication: bool=False,
                 chunk_size: int=512,
                 chunk_overlap: int=128,
                 separators=['\n\n\n', '\n\n', '\n', ' '],
                 separators_md=['###', '##', '#', '\n'],
                 embedding_model_path: str=None,
                 repo_id: str=None,
                 offline: bool=False):
        """Chroma database class initialiser."""
        # pylint: disable=dangerous-default-value  # List of separators, this is OK.
        self._path = path
        self._cname = collection
        self._split_text = split_text
        self._allowdups = allow_duplication
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._sep = separators
        self._sepmd = separators_md
        self._embpath = embedding_model_path
        self._repo_id = repo_id
        self._offline = offline
        self._dbo = None            # Database object.
        self._docs = []             # List of 'Document' objects.
        self._docss = []            # List of 'Document' objects *with splits*.
        self._fbase = None          # Basename of the document currently being loaded.
        self._fpath = None          # Full path to the document currently being loaded.
        self._from_md = False       # Load the PDF from Markdown format.
        self._p = None              # Document parser object.
        self._splitter = None       # Text splitter.
        self._set_db_client()
        self._check_parameters()

    @property
    def chroma(self):
        """Accessor to the database client object."""
        return self._dbo

    @property
    def parser(self):
        """Accessor to the document parser object."""
        return self._p

    def _already_loaded(self) -> bool:
        """Test if the file has already been loaded into the collection.

        :Logic:
            This test is performed by querying the collection for a
            metadata 'source' which equals the filename. As this uses
            a chromadb 'filter' (i.e. ``$eq``), testing for partial
            matches is not possible at this time.

            If the filename is different (in any way) from the source's
            filename in the database, the file will be loaded again.

        Returns:
            bool: False if the allow duplication flag is set. Or, True
            is the *exact* filename was found in the collection's
            metadata, otherwise False.

        """
        if self._allowdups:
            return False
        if self._dbo.collection.get(where={'source': {'$eq': self._fbase}})['ids']:
            print(f'-- File already loaded: {self._fbase} - skipping')
            return True
        return False

    def _check_parameters(self) -> None:
        """Verify the class parameters are viable.

        :Checks:
            - If ``offline``, ensure the embedding model path is
              provided.

        Raises:
            ValueError: If an instance is created in offline mode and an
            embedding model path is not provided, or does not exist.

        """
        if self._offline and (not self._embpath or not os.path.exists(self._embpath)):
            raise ValueError('When running in offline mode, the path to an embedding model '
                             'must be provided.')

    def _load(self, path: str, **kwargs):
        """Load the provided file into the vector store.

        Args:
            path (str): Full path to the file to be loaded.

        :Keyword Arguments:
            Those passed from the document-type-specific loader's
            :func:`load` method.

        """
        # pylint: disable=multiple-statements
        self._fpath = path
        self._fbase = os.path.basename(path)
        if self._already_loaded():
            return
        self._set_parser()
        s = self._set_text_splitter()
        if s: s = self._parse_text(**kwargs)
        if s: s = self._split_texts()
        if s: s = self._remove_duplicate_chunks()
        if s: s = self._load_worker()
        self._print_summary(success=s)

    def _remove_duplicate_chunks(self) -> bool:
        """Remove any duplicated Document objects.

        When loading, any duplicated document objects will be assigned
        the same ID for the database, which causes a duplication error.
        This is a pre-emptive measure to remove any duplication ahead of
        the load.

        Returns:
            bool: True if the filtered documents are populated, otherwise
            False.

        """
        # As the Document object is unhashable (and order matters), this has
        # to be done the old school way.
        tmp = []
        for doc in self._docss:
            if not doc in tmp:
                tmp.append(doc)
        self._docss = tmp[:]
        return bool(self._docss)

    def _load_worker(self) -> bool:
        """Load the split documents into the database collection.

        Returns:
            bool: True if loaded successfully, otherwise False. Success
            is based on the number of records after the load being
            greater than the number of records before the load, or not
            exceptions being raised.

        """
        # pylint: disable=line-too-long
        try:
            print('- Loading the document into the database ...')
            nrecs_b = self._dbo.collection.count()  # Count records before.
            self._dbo.add_documents(self._docss)
            nrecs_a = self._dbo.collection.count()  # Count records after.
            return self._test_load(nrecs_b=nrecs_b, nrecs_a=nrecs_a)
        except chromadberrors.DuplicateIDError:  # nocover  # Should be unreachable (dups removed).
            print('  -- Document *chunk* already loaded, duplication detected. File may be corrupt.')
            return False  # Prevent from loading keywords.
        except Exception as err:
            reporterror(err)
        return False  # nocover  # Should be unreachable.

    def _parse_text(self, **kwargs) -> bool:
        """Stub method, overridden by the child class."""

    @staticmethod
    def _print_summary(success: bool):
        """Print an end of processing summary.

        Args:
            success (bool): Success flag from the processor.

        """
        if success:
            print('Processing complete. Success.')
        else:
            print('Processing aborted due to error. Failure.')

    def _set_db_client(self) -> bool:
        """Set the database client object.

        If the ``_db`` object is a string, this is inferred as the *path*
        to the database. Otherwise, it is inferred as the database object
        itself.

        Returns:
            bool: True if the database object is set without error.
            Otherwise False.

        """
        try:
            if isinstance(self._path, str):
                self._dbo = ChromaDB(path=self._path,
                                     collection=self._cname,
                                     embedding_model_path=self._embpath,
                                     repo_id=self._repo_id,
                                     offline=self._offline)
            else:
                self._dbo = self._path
        except Exception as err:
            reporterror(err)
            return False
        return True

    def _set_parser(self):
        """Stub method, overridden by the child class."""

    def _set_text_splitter(self) -> bool:
        """Define the text splitter to be used.

        Returns:
            bool: True, always.

        """
        # Use different separators for a Markdown file.
        sep = self._sepmd if os.path.splitext(self._fpath)[1].lower() == '.md' else self._sep
        if self._from_md:
            sep = self._sepmd
        self._splitter = RecursiveCharacterTextSplitter(chunk_size=self._chunk_size,
                                                        chunk_overlap=self._chunk_overlap,
                                                        separators=sep)
        return True

    def _split_texts(self) -> bool:
        """Split the document text using a recursive text splitter.

        Note:
            If the ``split_text`` parameter was passed as ``False`` on
            instantiation, the texts will not be split. Rather, the
            :attr:`_docs` list is simply *copied* to the :attr:`_docss`
            attribute.

        Returns:
            bool: True if the text was split (or copied) successfully,
            otherwise False.

        """
        if self._split_text:
            self._docss = self._splitter.split_documents(self.parser.doc.documents)
        else:
            self._docss = self.parser.doc.documents[:]
        if not self._docss:  # nocover  # Should be unreachable.
            msg = (f'{self._PFX_ERR} An error occurred while splitting the documents for '
                   f'{self._fbase}.')
            ui.print_warning(msg)
            return False
        return True

    def _test_load(self, nrecs_b: int, nrecs_a: int) -> bool:
        """Test the document was loaded successfully.

        :Test:
            - Given a count of records before the load, verify the number
              of records after the load is equal to the number of records
              before, plus the number of split documents.

        Args:
            nrecs_b (int): Number of records *before* the load.
            nrecs_a (int): Number of records *after* the load.

        Returns:
            bool: True if the number of records before the load plus the
            number is splits is equal to the number of records after the
            load.

        """
        if nrecs_a == nrecs_b:
            ui.print_warning(f'{self._PFX_WARN} No new documents added. Possibly already loaded?')
        return nrecs_a == nrecs_b + len(self._docss)
