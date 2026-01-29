#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long  # Hyperlinks
"""
:Purpose:   This module provides the implementation for the project's
            ``Document`` object(s).

            These objects contain a document's page contents as well as
            any metadata associated with the document.

            .. important::

                The :class:`~Document` class is a ``docp``-based
                implementation of LangChain's `Document <document_>`_
                object to decrease library dependencies and provide us flexibility
                to configure the object as needed.

                However, this object **must** be (and remain) compatible
                with LangChain's `text splitters <splitter_>`_ and `Chroma <chroma_>`_
                objects, as they are passed directly into the these
                objects.

                .. _document: https://reference.langchain.com/python/
                   langchain_core/documents/#langchain_core.documents
                .. _splitter: https://docs.langchain.com/oss/python/
                   integrations/splitters
                .. _chroma: https://docs.langchain.com/oss/python/
                   integrations/vectorstores/chroma

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""


class Document:
    """Object used to store a document's content and metadata.

    Args:
        page_content (str): A single string containing a page's text
            content.
        metadata (dict, optional): Any metadata to be associated to the
            document. Defaults to None.

    """

    def __init__(self, page_content: str, *, metadata: dict=None) -> None:
        """Document class initialiser."""
        self._pc = page_content
        self._m = metadata

    @property
    def metadata(self) -> dict:
        """Accessor to a document's metadata."""
        if self._m:
            return self._m
        return {}

    @property
    def page_content(self) -> str:
        """Accessor to a document's page contents as a single string."""
        return self._pc
