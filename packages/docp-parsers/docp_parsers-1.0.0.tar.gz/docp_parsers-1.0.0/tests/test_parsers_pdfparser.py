#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``parsers.pdfparser`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

# pylint: disable=import-error
"""
# pylint: disable=invalid-name      # (e.g. exp_pgN)
# pylint: disable=protected-access  # _tbl_opath
# pylint: disable=no-member         # (e.g. marked_content, tables)

import contextlib
import inspect
import io
import os
import shutil
from utils4.crypto import crypto
# locals
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_parsers.parsers.pdfparser import PDFParser

_MODULE = os.path.splitext(__name__)[0]


class TestPDFParser(TestBase):
    """Testing class used to test the ``parsers.pdfparser`` module."""
    # pylint: disable=too-many-public-methods

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='parsers.pdfparser')
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
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '954e9f92f8d49d7229d16cf9061599b4'
        exp_pgN = '1857ba8a56a692f845cf53bf1fe0911d'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01b__extract_text__x_tolerance(self):
        """Test the ``extract_text`` method with an updated x_tolerance.

        :Test:
            - Verify the extracted text is a expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True,
                         x_tolerance=2)  # Split wordswhicharejoined
        exp_pg1 = '2188b5d6ad974dafdf22464d29fc4fe1'
        exp_pgN = '63811c923187045c98e618ea2d66d10c'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01c__extract_text__remove_newlines(self):
        """Test the ``extract_text`` method with newlines removed.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=True,  # <-- Changed
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '07bb0741a2cd9af79a4eeaa653ae4c72'
        exp_pgN = '7bab0e9652d62b09381280a4801d30aa'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01d__extract_text__keep_header_footer(self):
        """Test the ``extract_text`` method keeping the header/footer.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-untagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=False,  # <-- Changed
                         remove_footer=False,  # <-- Changed
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '64ac6d4af2b1ce3ce5b9f89234a17b65'
        exp_pgN = '76d7da6399e527fd4ac99449bb63819d'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01e__extract_text__remove_header(self):
        """Test the ``extract_text`` method removing the header.

        :Test:
            - Verify the extracted text is a expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-untagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,  # <-- Changed
                         remove_footer=False,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '1095b7726f76e38c9236e08c0eaeb760'
        exp_pgN = '1b67f4ad2ec5c302225fc30c3a43f838'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01f__extract_text__remove_footer(self):
        """Test the ``extract_text`` method removing the footer.

        :Test:
            - Verify the extracted text is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-untagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=False,
                         remove_footer=True,  # <-- Changed
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = 'cdf9a50257a13988db846ef8f6efdbfa'
        exp_pgN = '712e536e5490b7a197505f072b66d9f9'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01g__extract_text__long(self):
        """Test the ``extract_text`` method for a long(er) file.

        :Test:
            - Verify the extracted text is a expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-15-untagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=False,
                         remove_footer=False,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '11fa8ace989c9695eab51d453fbc19dc'
        exp_pgN = '131e774f286b1d4a4e7982d82e799621'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test01h__extract_text__short(self):
        """Test the ``extract_text`` method for a short file.

        :Test:
            - Attempt to remove header and footer, however as the
              document is short, the parser cannot search for common
              lines.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-untagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '11fa8ace989c9695eab51d453fbc19dc'
        exp_pgN = '4618c99f3fffa5f4894ad8b1f4419c14'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertFalse(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test02a__extract_text__tagged(self):
        """Test the ``extract_text`` method with a tagged file.

        :Test:
            - Verify the extracted text is a expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = 'eac8dd0155ecce0320e1a0285ad5e240'
        exp_pgN = 'c2a69b064156a25dd006e0ba3604a17b'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertTrue(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test02b__extract_text__tagged_remove_newlines(self):
        """Test the ``extract_text`` method with a tagged file.

        :Test:
            - Verify the extracted text is a expected, with newline
              characters removed.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=True,  # <-- Changed
                         ignore_tags=None,
                         convert_to_ascii=True)
        exp_pg1 = '59ce2bc6938916e317268ea19be9616b'
        exp_pgN = '43088c73e1922905796cab67004d3baf'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test02c__extract_text__keep_header_footer(self):
        """Test the ``extract_text`` method, ignoring no tags.

        :Test:
            - Verify the header and footer are kept from a tagged PDF
              file.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags='na',  # <-- Include header/footer
                         convert_to_ascii=True)
        exp_pg1 = '02d5bde9f6412bd63ec1cac18bab4e55'
        exp_pgN = 'd6b7b64e51f3fcf78af8333f163f3b45'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertTrue(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test02d__extract_text__remove_header_footer(self):
        """Test the ``extract_text`` method, ignoring no tags.

        :Test:
            - Verify the header and footer are removed successfully from
              a tagged PDF file.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-5-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,  # <-- Removes header and footer
                         convert_to_ascii=True)
        exp_pg1 = 'd0f7cf518e2eea0b8097bcc1f9325e51'
        exp_pgN = '9f1a86e35d4dd50aa9a17ac455e184e4'
        tst1_pg1 = crypto.md5(pdf.pages[1].content)
        tst1_pgN = crypto.md5(pdf.pages[-1].content)
        tst2_pg1 = crypto.md5(pdf.doc.documents[0].page_content)
        tst2_pgN = crypto.md5(pdf.doc.documents[-1].page_content)
        self.assertTrue(pdf.doc.marked_content)
        self.assertEqual(exp_pg1, tst1_pg1)
        self.assertEqual(exp_pgN, tst1_pgN)
        self.assertEqual(exp_pg1, tst2_pg1)
        self.assertEqual(exp_pgN, tst2_pgN)

    def test03a__extract_text__force_reinitialise(self):
        """Test the ``extract_text`` method.

        :Test:
            - Call the ``extract_text`` twice to force an object
              reinitialisation. This ensures if a document is parsed
              twice, the page count, etc. is not duplicated.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-header-footer.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        self.assertEqual(len(pdf.pages), 3)
        pdf.extract_text(remove_header=True,
                         remove_footer=True,
                         remove_newlines=False,
                         ignore_tags=None,
                         convert_to_ascii=True)
        self.assertEqual(len(pdf.pages), 3)

    def test04a__extract_text__bad_file(self):
        """Test the ``extract_text`` method for a non-PDF file.

        :Test:
            - Verify a TypeError is raised for a non-PDF file.

        """
        path = os.path.join(self._DIR_FILES_PPTX, 'test-file-sm.pptx')
        with self.assertRaises(TypeError):
            PDFParser(path=path)

    def test05a__extract_tables(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=False,
                           verbose=False)
        self.assertEqual(pdf.doc.ntables, 2)
        self.assertEqual(len(pdf.tables), 2)
        # Content is tested later.

    def test05b__extract_tables__as_dataframe__table_1(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file and verify the DataFrame
              objects are as expected.

        """
        me = inspect.stack()[0].function
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=True,  # <-- Changed
                           to_csv=False,
                           verbose=False)
        exp = self.read_pickle(module=_MODULE, method=me)
        self.assertTrue(exp.equals(pdf.tables[0]))

    def test05c__extract_tables__as_dataframe__table_2(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file and verify the DataFrame
              objects are as expected.

        """
        me = inspect.stack()[0].function
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=True,  # <-- Changed
                           to_csv=False,
                           verbose=False)
        exp = self.read_pickle(module=_MODULE, method=me)
        self.assertTrue(exp.equals(pdf.tables[1]))

    def test05d__extract_tables__to_csv(self):
        """Test the ``extract_tables`` method for a table written to CSV.

        :Test:
            - Extract tables from a PDF file and verify the CSV output
              file is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=True,  # <-- Changed
                           verbose=False)
        exp = '8225c400968d9a2c4c5b02ae6ada4fe7'
        tst = crypto.checksum_md5(path=os.path.join(pdf._tbl_opath, 'pg001_tb001.csv'))
        self.assertEqual(exp, tst)
        # Cleanup
        shutil.rmtree(pdf._tbl_opath)

    def test05e__extract_tables__verbose(self):
        """Test the ``extract_tables`` method with verbose output.

        :Test:
            - Extract tables from a PDF file and verify the stdout is as
              expected.

        """
        buff = io.StringIO()
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        with contextlib.redirect_stdout(buff):
            pdf.extract_tables(table_settings=None,
                               as_dataframe=False,
                               to_csv=True,   # <-- Changed
                               verbose=True)  # <-- Changed
            tst = buff.getvalue()
        self.assertIn('Complete', tst)
        self.assertIn('2 tables were extracted', tst)
        self.assertIn(pdf._tbl_opath, tst)
        # Cleanup
        shutil.rmtree(pdf._tbl_opath)

    def test05f__extract_tables__force_reinitialise(self):
        """Test the ``extract_tables`` method.

        :Test:
            - Call the ``extract_tables`` twice to force an object
              reinitialisation. This ensures if a document is parsed
              twice, the tables are not duplicated.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'ca-warn-report-2.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=False,
                           verbose=False)
        self.assertEqual(len(pdf.tables), 2)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=False,
                           verbose=False)
        self.assertEqual(len(pdf.tables), 2)

    def test06a__extract_tables__untagged(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file.
            - Verify the content of the table(s) is as expected.

        """
        me = inspect.stack()[0].function
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-untagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=False,
                           verbose=False)
        exp = self.read_pickle(module=_MODULE, method=me)
        self.assertEqual(pdf.doc.ntables, 1)
        self.assertEqual(len(pdf.tables), 1)
        self.assertEqual(pdf.tables, exp)

    def test06b__extract_tables__tagged(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file.
            - Verify the content of the table(s) is as expected.

        """
        me = inspect.stack()[0].function
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=False,
                           verbose=False)
        exp = self.read_pickle(module=_MODULE, method=me)
        self.assertEqual(pdf.doc.ntables, 1)
        self.assertEqual(len(pdf.tables), 1)
        self.assertEqual(pdf.tables, exp)

    def test06c__extract_tables__as_dataframe(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file.
            - Verify the content of the table(s), extracted to a
              DataFrame, is as expected.

        """
        me = inspect.stack()[0].function
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=True,  # <- Changed
                           to_csv=False,
                           verbose=False)
        exp = self.read_pickle(module=_MODULE, method=me)
        self.assertEqual(pdf.doc.ntables, 1)
        self.assertEqual(len(pdf.tables), 1)
        self.assertTrue(exp[0].equals(pdf.tables[0]))

    def test06d__extract_tables__to_csv(self):
        """Test the ``extract_tables`` method for a PDF file.

        :Test:
            - Extract tables from a PDF file.
            - Verify the content of the table(s), extracted to a
              CSV file, is as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-header-footer-table.pdf')
        pdf = PDFParser(path=path)
        pdf.extract_tables(table_settings=None,
                           as_dataframe=False,
                           to_csv=True,  # <- Changed
                           verbose=False)
        exp = '685fb9828bec03e939355879022ba6bb'
        tst= self.get_checksum(path=os.path.join(pdf._tbl_opath, 'pg001_tb001.csv'))
        self.assertEqual(pdf.doc.ntables, 1)
        self.assertEqual(len(pdf.tables), 1)
        self.assertEqual(exp, tst)
        # Cleanup
        shutil.rmtree(pdf._tbl_opath)
