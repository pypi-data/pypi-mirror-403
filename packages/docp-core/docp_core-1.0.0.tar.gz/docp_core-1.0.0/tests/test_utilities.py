#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``utilities`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import os
from glob import glob
from utils4.crypto import crypto
# locals
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_core.utilities import utilities


class TestUtilities(TestBase):
    """Testing class used to test the ``utilities`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='utilities')

    def test01a__collect_files(self):
        """Test the ``collect_files`` method for all files.

        :Test:
            - Verify the method returns the expected list of files.

        """
        exp = glob(os.path.join(self._DIR_FILES, '**'), recursive=True)
        tst = utilities.collect_files(path=self._DIR_FILES, ext='**', recursive=True)
        exp_ = list(filter(os.path.isfile, exp))  # Exclude directories.
        self.assertEqual(exp_, tst)

    def test01b__collect_files__pdf(self):
        """Test the ``collect_files`` method for PDF files.

        :Test:
            - Verify the method returns the expected list of PDF files.

        """
        exp = glob(os.path.join(self._DIR_FILES_PDF, '*.pdf'))
        tst = utilities.collect_files(path=self._DIR_FILES_PDF, ext='pdf')
        self.assertEqual(exp, tst)

    def test01c__collect_files__pptx(self):
        """Test the ``collect_files`` method for PPTX files.

        :Test:
            - Verify the method returns the expected list of PPTX files.

        """
        exp = glob(os.path.join(self._DIR_FILES_PPTX, '*.pptx'))
        tst = utilities.collect_files(path=self._DIR_FILES_PPTX, ext='pptx')
        self.assertEqual(exp, tst)

    def test02a__ispdf(self):
        """Test the ``ispdf`` method for actual PDF files.

        :Test:
            - Verify the test shows True for (n) valid PDF files.

        """
        files = utilities.collect_files(path=self._DIR_FILES_PDF, ext='pdf')
        for path in files:
            with self.subTest(msg=os.path.basename(path)):
                self.assertTrue(utilities.ispdf(path=path))

    def test02b__ispdf__false(self):
        """Test the ``ispdf`` method for non-PDF files.

        :Test:
            - Verify the test shows False for (n) non-PDF files.

        """
        files = utilities.collect_files(path=self._DIR_FILES_PPTX, ext='pptx')
        for path in files:
            with self.subTest(msg=os.path.basename(path)):
                self.assertFalse(utilities.ispdf(path=path))

    def test03a__iszip(self):
        """Test the ``iszip`` method for actual PPTX files.

        :Test:
            - Verify the test shows True for (n) valid PPTX files.

        """
        files = utilities.collect_files(path=self._DIR_FILES_PPTX, ext='pptx')
        for path in files:
            with self.subTest(msg=os.path.basename(path)):
                self.assertTrue(utilities.iszip(path=path))

    def test03b__iszip__false(self):
        """Test the ``iszip`` method for non-PPTX files.

        :Test:
            - Verify the test shows False for (n) non-PPTX files.

        """
        files = utilities.collect_files(path=self._DIR_FILES_PDF, ext='pdf')
        for path in files:
            with self.subTest(msg=os.path.basename(path)):
                self.assertFalse(utilities.iszip(path=path))

    def test04a__parse_to_keywords__asterisk(self):
        """Test the ``parse_to_keywords`` method for asterisk bullet points.

        :Test:
            - Verify the method returns the expected list of values.

        """
        resp = 'This is a list of keywords: * Americano\n* Latte\n* Mocha\n* Flat White'
        exp = 'americano, latte, mocha, flat white'
        tst = utilities.parse_to_keywords(resp=resp)
        self.assertEqual(exp, tst)

    def test04b__parse_to_keywords__hyphen(self):
        """Test the ``parse_to_keywords`` method for hyphen bullet points.

        :Test:
            - Verify the method returns the expected list of values.

        """
        resp = 'This is a list of keywords: - Americano\n- Latte\n- Mocha\n- Flat White'
        exp = 'americano, latte, mocha, flat white'
        tst = utilities.parse_to_keywords(resp=resp)
        self.assertEqual(exp, tst)

    def test04c__parse_to_keywords__numbered1(self):
        """Test the ``parse_to_keywords`` method for numbered bullet points.

        :Test:
            - Verify the method returns the expected list of values.

        """
        resp = 'This is a list of keywords: 1. Americano\n2. Latte\n3. Mocha\n4. Flat White'
        exp = 'americano, latte, mocha, flat white'
        tst = utilities.parse_to_keywords(resp=resp)
        self.assertEqual(exp, tst)

    def test04d__parse_to_keywords__numbered2(self):
        """Test the ``parse_to_keywords`` method for numbered bullet points.

        :Test:
            - Verify the method returns the expected list of values.

        """
        resp = 'This is a list of keywords: 1) Americano\n2) Latte\n3) Mocha\n4) Flat White'
        exp = 'americano, latte, mocha, flat white'
        tst = utilities.parse_to_keywords(resp=resp)
        self.assertEqual(exp, tst)

    def test04e__parse_to_keywords__null(self):
        """Test the ``parse_to_keywords`` method for an unparsable string.

        :Test:
            - Verify the method returns an empty string as keywords
              cannot be extracted.

        """
        resp = 'This is a list of keywords: Americano\nLatte\nMocha\nFlat White'
        exp = ''
        tst = utilities.parse_to_keywords(resp=resp)
        self.assertEqual(exp, tst)

    def test05a__build_project_outpath(self):
        """Test the ``build_project_outpath`` method.

        :Test:
            - Verify the method returns the expected path(s).

        """
        tests = ('one', 'one/two', 'one/two/three')
        for test in tests:
            tst = utilities.build_project_outpath(subpath=test)
            exp = os.path.join(os.path.expanduser('~/Desktop'), 'docp', test)
            self.assertEqual(exp, tst)

    def test06a__remove_duplicate_lines(self):
        """Test the ``remove_duplicate_lines`` method.

        :Test:
            - Verify the method removes duplicates lines as expected.

        """
        with open(os.path.join(self._DIR_FILES_TXT, 'duplicated-lines.txt'), encoding='ascii') as f:
            text = f.read()
        exp = '15119e389ec484c2d8d5b6711c8f408f'
        tst = crypto.md5(utilities.remove_duplicate_lines(text=text))
        self.assertEqual(exp, tst)
