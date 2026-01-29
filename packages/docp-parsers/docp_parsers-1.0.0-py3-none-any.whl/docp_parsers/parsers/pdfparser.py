#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module serves as the public interface for interacting
            with PDF files and parsing their contents.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

:Example:   For example code usage, please refer to the
            :class:`PDFParser` class docstring.

"""

# locals
try:
    from ._pdftableparser import _PDFTableParser
    from ._pdftextparser import _PDFTextParser
except ImportError:
    from docp_parsers.parsers._pdftableparser import _PDFTableParser
    from docp_parsers.parsers._pdftextparser import _PDFTextParser


class PDFParser(_PDFTableParser, _PDFTextParser):
    """PDF document parser.

    Args:
        path (str): Full path to the PDF document to be parsed.

    :Example:

        Extract text from a PDF file::

            >>> from docp_parsers import PDFParser

            >>> pdf = PDFParser(path='/path/to/myfile.pdf')
            >>> pdf.extract_text()

            # Access the content of page 1.
            >>> pg1 = pdf.pages[1].content
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit,
             sed do eiusmod tempor incididunt ut labore et dolore magna
             aliqua.'

        Extract tables from a PDF file::

            >>> from docp_parsers import PDFParser

            >>> pdf = PDFParser('/path/to/myfile.pdf')
            >>> pdf.extract_tables()

            # Access the first table.
            >>> tbl1 = pdf.tables[1]

    """

    def __init__(self, path: str):
        """PDF parser class initialiser."""
        super().__init__(path=path)
