#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``objects`` package.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  This object testing module is used to test the methods which
            are left untested by the XParser black-box tests.

            This is *not* an extensive unittesting module.

"""

import os
from docp_core.objects.textobject import TextObject
# locals
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_parsers.parsers.pdfparser import PDFParser
from docp_parsers.parsers.pptxparser import PPTXParser


class TestDocBaseObject(TestBase):
    """Testing class used to test the ``_docbaseobject`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='objects._docbaseobject')

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the start of all test cases."""

    def test01a__filepath(self):
        """Test the ``filepath`` attribute.

        :Test:
            - Verify the attribute value is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        exp = path
        tst = pdf.doc.filepath
        self.assertEqual(exp, tst)

    def test01b__filepath(self):
        """Test the ``filepath`` attribute.

        :Test:
            - Verify the attribute value is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        exp = path
        tst = pdf.doc.filepath
        self.assertEqual(exp, tst)

    def test02a__metadata(self):
        """Test the ``metadata`` attribute.

        :Test:
            - Verify the attribute value is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        exp = {'Author': '',
               'CreationDate': "D:20210413004838+00'00'",
               'Creator': 'LaTeX with hyperref',
               'ModDate': "D:20210413004838+00'00'",
               'Producer': 'pdfTeX-1.40.21'}
        tst = pdf.doc.metadata
        self.assertEqual(exp, tst)

    def test02b__metadata(self):
        """Test the ``metadata`` attribute.

        :Test:
            - Verify the attribute value is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        exp = {'Creator': 'Writer',
               'Producer': 'LibreOffice 24.2',
               'CreationDate': "D:20251215132947Z'"}
        tst = pdf.doc.metadata
        self.assertEqual(exp, tst)


class TestPageObject(TestBase):
    """Testing class used to test the ``_pageobject`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='objects._pageobject')

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the start of all test cases."""

    def test01a__repr(self):
        """Test the ``__repr__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text()
        tst = repr(pdf.pages[1])
        exp = f'<Page: {pdf.pages[1].pageno}; Chars: {len(pdf.pages[1].content)}>'
        self.assertEqual(exp, tst)

    def test01b__repr(self):
        """Test the ``__repr__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text()
        tst = repr(pdf.pages[-1])
        exp = f'<Page: {pdf.pages[-1].pageno}; Chars: {len(pdf.pages[-1].content)}>'
        self.assertEqual(exp, tst)

    def test01c__repr__index_zero(self):
        """Test the ``__repr__`` method for for offset index.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        tst = repr(pdf.pages[0])
        exp = '<Page: 0; <index offset>>'
        self.assertEqual(exp, tst)

    def test02a__str(self):
        """Test the ``__str__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text()
        tst = str(pdf.pages[1])
        exp = ('Page no: 1; Content: "Retrieval-Augmented Gener ..."; '
               'Chars: 2602; nTables: 0; Parser avail: True')
        self.assertEqual(exp, tst)

    def test03a__parser(self):
        """Test the ``parser`` attribute.

        :Test:
            - Verify the object accessed is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text()
        self.assertTrue(hasattr(pdf.pages[1].parser, 'extract_text'))

    def test04a__show(self):
        """Test the ``show`` method.

        :Test:
            - Verify the object returned by the method is an ``Image``
              object.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text()
        exp = "<class 'PIL.Image.Image'>"
        tst = str(type(pdf.pages[1].show().original))
        self.assertEqual(exp, tst)


class TestSlideObject(TestBase):
    """Testing class used to test the ``_slideobject`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='objects._slideobject')

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the start of all test cases."""

    def test01a__repr(self):
        """Test the ``__repr__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        tst = repr(pptx.slides[1])
        exp = f'<Slide: {pptx.slides[1].pageno}; Text blocks: {len(pptx.slides[1].texts)}>'
        self.assertEqual(exp, tst)

    def test01b__repr(self):
        """Test the ``__repr__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        tst = repr(pptx.slides[-1])
        exp = f'<Slide: {pptx.slides[-1].pageno}; Text blocks: {len(pptx.slides[-1].texts)}>'
        self.assertEqual(exp, tst)

    def test01c__repr__index_zero(self):
        """Test the ``__repr__`` method for for offset index.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        tst = repr(pptx.slides[0])
        exp = '<Slide: 0; <index offset>>'
        self.assertEqual(exp, tst)

    def test02a__str(self):
        """Test the ``__str__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        tst = str(pptx.slides[1])
        exp = '<Slide: 1; Text blocks: 2; Tables: 0; Images: 0; Parser: True>'
        self.assertEqual(exp, tst)

    def test02b__str__index_zero(self):
        """Test the ``__str__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        tst = str(pptx.slides[0])
        exp = '<Slide: 0; <index offset>>'
        self.assertEqual(exp, tst)

    def test03a__parser(self):
        """Test the ``parser`` attribute.

        :Test:
            - Verify the object accessed is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        self.assertTrue(hasattr(pptx.slides[1].parser, 'shapes'))


class TestTextObject(TestBase):
    """Testing class used to test the ``_textobject`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='objects._textobject')

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the start of all test cases."""

    def test01a__str(self):
        """Test the ``__str__`` method.

        :Test:
            - Verify the text displayed to stdout is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        exp = pptx.slides[1].texts[0].content
        tst = str(pptx.slides[1].texts[0])
        self.assertEqual(exp, tst)

    def test02a__content_setter(self):
        """Test the object's ``content`` setter method.

        :Test:
            - Verify the value added to the object's ``content``
              attribute is as excpected.

        """
        text = 'Some content here.'
        t = TextObject(content=None)
        self.assertIsNone(t.content)
        self.assertFalse(t.hastext)
        t.content = text
        self.assertEqual(t.content, text)
        self.assertTrue(t.hastext)
