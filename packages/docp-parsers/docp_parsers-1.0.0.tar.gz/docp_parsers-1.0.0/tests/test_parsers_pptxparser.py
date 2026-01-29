#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``parsers.pptxparser`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error
# pylint: disable=invalid-name      # (e.g. exp_pgN)
# pylint: disable=protected-access  # _tbl_opath
# pylint: disable=no-member         # (e.g. marked_content, tables)

import os
from utils4.crypto import crypto
# locals
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_parsers.parsers.pptxparser import PPTXParser

_MODULE = os.path.splitext(__name__)[0]


class TestPPTXParser(TestBase):
    """Testing class used to test the ``parsers.pptxparser`` module."""
    # pylint: disable=too-many-public-methods

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='parsers.pptxparser')
        cls.ignore_warnings()

    @classmethod
    def tearDownClass(cls):
        """Run this logic at the start of all test cases."""
        cls.reset_warnings()

    def test01a__extract_text(self):
        """Test the ``extract_text`` method.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text(remove_newlines=False,
                          convert_to_ascii=True)
        exp_pg1 = 'a66d6aec3dc69ce2140d89dc90b52db8'
        exp_pgN = '10fa40f89acb2cd91f1529205f236237'
        tst_pg1 = crypto.md5(pptx.slides[1].content)
        tst_pgN = crypto.md5(pptx.slides[-1].content)
        self.assertEqual(exp_pg1, tst_pg1)
        self.assertEqual(exp_pgN, tst_pgN)

    def test01b__extract_text(self):
        """Test the ``extract_text`` method.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-lg.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text(remove_newlines=False,
                          convert_to_ascii=True)
        exp_pg1 = 'a66d6aec3dc69ce2140d89dc90b52db8'
        exp_pgM = '4560f1b32b9657033ad30b3b92c8ed13'
        exp_pgN = 'f3631afd8df19ee571a329037c896c62'
        tst_pg1 = crypto.md5(pptx.slides[1].content)
        tst_pgM = crypto.md5(pptx.slides[10].content)
        tst_pgN = crypto.md5(pptx.slides[-1].content)
        self.assertEqual(exp_pg1, tst_pg1)
        self.assertEqual(exp_pgM, tst_pgM)
        self.assertEqual(exp_pgN, tst_pgN)

    def test01c__extract_text__remove_newlines(self):
        """Test the ``extract_text`` method.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text(remove_newlines=True,  # <-- Changed
                          convert_to_ascii=True)
        exp_pg1 = 'a66d6aec3dc69ce2140d89dc90b52db8'
        exp_pgN = '10fa40f89acb2cd91f1529205f236237'
        tst_pg1 = crypto.md5(pptx.slides[1].content)
        tst_pgN = crypto.md5(pptx.slides[-1].content)
        self.assertEqual(exp_pg1, tst_pg1)
        self.assertEqual(exp_pgN, tst_pgN)

    def test01d__extract_text__remove_newlines(self):
        """Test the ``extract_text`` method.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-lg.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text(remove_newlines=True,  # <-- Changed
                          convert_to_ascii=True)
        exp_pg1 = 'a66d6aec3dc69ce2140d89dc90b52db8'
        exp_pgM = '4560f1b32b9657033ad30b3b92c8ed13'
        exp_pgN = 'f3631afd8df19ee571a329037c896c62'
        tst_pg1 = crypto.md5(pptx.slides[1].content)
        tst_pgM = crypto.md5(pptx.slides[10].content)
        tst_pgN = crypto.md5(pptx.slides[-1].content)
        self.assertEqual(exp_pg1, tst_pg1)
        self.assertEqual(exp_pgM, tst_pgM)
        self.assertEqual(exp_pgN, tst_pgN)

    def test01e__extract_text__force_reinitialise(self):
        """Test the ``extract_text`` method.

        :Test:
            - Call the ``text`` twice to force an object
              reinitialisation. This ensures if a document is parsed
              twice, the tables are not duplicated.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        pptx = PPTXParser(path=path)
        pptx.extract_text()
        self.assertEqual(len(pptx.slides), 6)
        pptx.extract_text()
        self.assertEqual(len(pptx.slides), 6)

    def test01f__extract_text__bad_file(self):
        """Test the ``extract_text`` method for a non-PPTX file.

        :Test:
            - Verify a TypeError is raised for a non-PPTX file.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        with self.assertRaises(TypeError):
            PPTXParser(path=path)
