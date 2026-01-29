#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the 'PDF Document' object structure into
            which PDF documents are parsed into for transport and onward
            use.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

try:
    from ._docbaseobject import _DocBase
    from ._pageobject import PageObject
except ImportError:
    from docp_parsers.objects._docbaseobject import _DocBase
    from docp_parsers.objects._pageobject import PageObject


class DocPDF(_DocBase):
    """Container class for storing data parsed from a PDF file."""

    def __init__(self):
        """PDF document object class initialiser."""
        super().__init__()
        self._tags = False
        self._pages = [PageObject(pageno=0)]    # List of PageObjects, offset by 1 to align
                                                # the index with page numbers.
        self._tables = []                       # List of extracted table objects.

    @property
    def pages(self) -> list[PageObject]:
        """A list of containing an object for each page in the document.

        .. tip::

            The page number index aligns to the page number in the PDF
            file.

            For example, to access the ``PageObject`` for page 42, use::

                pages[42]

       """
        return self._pages

    @property
    def marked_content(self) -> bool:
        """Indicate if the document was parsed using marked-content tags.

        PDF documents can be created with 'marked content' tags. When
        a PDF document is parsed using tags, as this flag indicates, the
        parser respects columns and other page formatting schemes. If a
        multi-column page is parsed without tags, the parser reads
        straight across the line, thus corrupting the text.

        """
        return self._tags

    @property
    def tables(self) -> list:
        """Accessor to data extracted from a document's tables."""
        return self._tables
