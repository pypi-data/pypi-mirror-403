#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the project initilisation logic.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

# locals
try:
    from .libs._version import __version__
    from .parsers.pdfparser import PDFParser
    from .parsers.pptxparser import PPTXParser
except ImportError:
    from docp_parsers.libs._version import __version__
    from docp_parsers.parsers.pdfparser import PDFParser
    from docp_parsers.parsers.pptxparser import PPTXParser

