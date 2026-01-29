#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``parsers.pdfparser`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import contextlib
import logging
import os
from utils4.crypto import crypto
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_core.objects.textobject import TextObject
from docp_docling import PDFParser

# Silence logging output. Cannot seem to silence the output for RapidOCR.
_logger_docling = logging.getLogger('docling')
_logger_docling.setLevel(logging.ERROR)


class TestPDFParser(TestBase):
    """Testing class used to test the ``parsers.pdfparser`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='parsers.pdfparser')
        cls.ignore_warnings()

    @classmethod
    def tearDownClass(cls):
        """Actions to be performed after all tests are complete."""
        cls.reset_warnings()

    def test01a__to_markdown(self):
        """Test the ``to_markdown`` method.

        :Test:
            - Verify the PDF to markdown conversion generates the
              markdown text as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_markdown(page_no=None,
                        image_mode='placeholder',
                        include_annotations=True,
                        unique_lines=False,
                        to_file=False,
                        auto_open=False)
        exp = '905c15dba022bf396dbc4db2d16c742e'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test01b__to_markdown__single_page(self):
        """Test the ``to_markdown`` method, for a single page.

        :Test:
            - Verify the PDF to markdown conversion generates the
              markdown text as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_markdown(page_no=1,  # <<- Changed
                        image_mode='placeholder',
                        include_annotations=True,
                        unique_lines=False,
                        to_file=False,
                        auto_open=False)
        exp = 'efe35b8c0c7824bb1d6467fa81a83228'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test01c__to_markdown__single_page__multi_run(self):
        """Test the ``to_markdown`` method, for an entire document.

        The document is iterated and converted a single page at a time.

        :Test:
            - Verify the PDF to markdown conversion generates the
              markdown text as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        for i in range(1, 3):
            pdf.to_markdown(page_no=i,  # <<- Changed
                            image_mode='placeholder',
                            include_annotations=True,
                            unique_lines=False,
                            to_file=False,
                            auto_open=False)
        exp = '0403b8fe0ce6389244e3f6d76934cb75'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test01d__to_markdown__to_file(self):
        """Test the ``to_markdown`` method; write the output to a file.

        :Test:
            - Verify the PDF to markdown conversion generates the text
              file as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        with contextlib.redirect_stdout(None):
            path = pdf.to_markdown(page_no=None,
                                   image_mode='placeholder',
                                   include_annotations=True,
                                   unique_lines=False,
                                   to_file=True,  # <-- Changed
                                   auto_open=False)
        exp = '783b051719458f26a72663179d181810'
        tst = crypto.checksum_md5(path=path)
        self.assertEqual(exp, tst)

    def test01e__to_markdown__unique(self):
        """Test the ``to_markdown`` method, removing repeated lines.

        :Test:
            - Verify the PDF to markdown conversion generates the text
              as expected, with repeated lines removed.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_markdown(page_no=None,
                        image_mode='placeholder',
                        include_annotations=True,
                        unique_lines=True,  # <-- Changed
                        to_file=False,
                        auto_open=False)
        exp = 'e3566468892863fbd7b01540a3c7029a'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test01f__to_markdown__embedded(self):
        """Test the ``to_markdown`` method, embedding an image.

        :Test:
            - Verify the PDF to markdown conversion generates the
              markdown file as expected, with an embedded image.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'test-file-02.pdf')
        pdf = PDFParser(path=path)
        with contextlib.redirect_stdout(None):
            path = pdf.to_markdown(page_no=1,  # <-- Changed
                                   image_mode='embedded',  # <-- Changed
                                   include_annotations=True,
                                   unique_lines=False,
                                   to_file=True,  # <-- Changed
                                   auto_open=False)
        exp = 'ee1fc9197f66856049dcb07ec56e34e2'
        tst = crypto.checksum_md5(path)
        self.assertEqual(exp, tst)

    def test02a__to_html(self):
        """Test the ``to_html`` method.

        :Test:
            - Verify the PDF to HTML conversion generates the HTML text
              as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-1-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_html(page_no=None,
                    image_mode='placeholder',
                    include_annotations=True,
                    unique_lines=False,
                    to_file=False,
                    auto_open=False)
        exp = 'f3fc0ce957225dc2ca6eae05c92735a2'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test02b__to_html__simgle_page(self):
        """Test the ``to_html`` method, for a single page.

        :Test:
            - Verify the PDF to HTML conversion generates the HTML text
              as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_html(page_no=1,  # <<- Changed
                    image_mode='placeholder',
                    include_annotations=True,
                    unique_lines=False,
                    to_file=False,
                    auto_open=False)
        exp = 'cdf804a109f7eaec210fd94a291f44a3'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test02c__to_html__simgle_page__multi_run(self):
        """Test the ``to_html`` method, for an entire document.

        The document is iterated and converted a single page at a time.

        :Test:
            - Verify the PDF to HTML conversion generates the HTML text
              as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        for i in range(1, 3):
            pdf.to_html(page_no=i,  # <<- Changed
                        image_mode='placeholder',
                        include_annotations=True,
                        unique_lines=False,
                        to_file=False,
                        auto_open=False)
        exp = 'd6e31755ce8d2537a78157093c08aacc'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test02d__to_html__to_file(self):
        """Test the ``to_html`` method; write the output to a file.

        :Test:
            - Verify the PDF to markdown conversion generates the HTML
              text file as expected.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        with contextlib.redirect_stdout(None):
            path = pdf.to_html(page_no=None,
                                image_mode='placeholder',
                                include_annotations=True,
                                unique_lines=False,
                                to_file=True,  # <-- Changed
                                auto_open=False)
        exp = '0daaeb4a8a65c8920a8f0f989904d7ce'
        tst = crypto.checksum_md5(path=path)
        self.assertEqual(exp, tst)

    def test02e__to_html__unique(self):
        """Test the ``to_html`` method, removing repeated lines.

        :Test:
            - Verify the PDF to HTML conversion generates the text
              as expected, with repeated lines removed.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_html(page_no=None,
                    image_mode='placeholder',
                    include_annotations=True,
                    unique_lines=True,  # <-- Changed
                    to_file=False,
                    auto_open=False)
        exp = 'c8bb8db75316c1a67c564ac48921ae54'
        tst = crypto.md5(pdf.content)
        self.assertEqual(exp, tst)

    def test03a__initialise(self):
        """Test the ``initialise`` method.

        :Test:
            - Run a PDF conversion and verify TextObjects exist.
              Initialise, and verify the TextObjects have been removed.

        """
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        pdf.to_markdown(page_no=None,
                        image_mode='placeholder',
                        include_annotations=True,
                        unique_lines=False,
                        to_file=False,
                        auto_open=False)
        self.assertEqual(len(pdf.texts), 1)
        self.assertIsInstance(pdf.texts[0], TextObject)
        pdf.initialise()
        self.assertEqual(len(pdf.texts), 0)

    def test04a___image_mode_override(self):
        """Test the ``_image_mode_override`` method.

        :Test:
            - Verify the ``generate_*_images`` attributes are set as
              expected.

        """
        # pylint: disable=protected-access  # OK for testing
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        keys = ('generate_page_images', 'generate_picture_images')
        for key in keys:
            self.assertFalse(getattr(pdf._conv.format_to_options['pdf'].pipeline_options, key))
        pdf._image_mode_override(image_mode='embedded')
        for key in keys:
            self.assertTrue(getattr(pdf._conv.format_to_options['pdf'].pipeline_options, key))

    def test04b___image_mode_override__bad(self):
        """Test the ``_image_mode_override`` method, with a bad value.

        :Test:
            - Verify the method raises an error when a bad image_mode
              value is provided.

        """
        # pylint: disable=protected-access  # OK for testing
        path = os.path.join(self._DIR_FILES_PDF, 'lorem-ipsum-2-tagged-headings.pdf')
        pdf = PDFParser(path=path)
        with self.assertRaises(ValueError):
            pdf._image_mode_override(image_mode='invalid')

    def test05a____set_pipeline_options__bad_model_path(self):
        """Test the ``_set_pipeline_options`` method, with a bad path.

        :Test:
            - Verify the method raises an error when an invalid model
              path is provided.

        """
        # pylint: disable=import-outside-toplevel  # OK for this case.
        # pylint: disable=invalid-name
        from docp_core import SETTINGS
        # Save a backup.
        _path = SETTINGS['paths']['models']['docling']
        # Hack the model to path something invalid.
        SETTINGS['paths']['models']['docling'] = '/path/does/not/exist'
        with self.assertRaises(FileNotFoundError):
            path = os.path.join(self._DIR_FILES_PDF, 'test-file-01.pdf')
            PDFParser(path=path)
        # Restore the path for future tests.
        SETTINGS['paths']['models']['docling'] = _path
