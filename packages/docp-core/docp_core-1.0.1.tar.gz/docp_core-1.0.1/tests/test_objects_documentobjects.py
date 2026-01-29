#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``objects.documentobjects`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_core.objects.documentobjects import Document


class TestDocument(TestBase):
    """Testing class used to test the ``objects.documentobjects`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='objects.documentobjects')

    def test01a__object(self):
        """Test the ``Document`` object itself.

        :Test:
            - Verify the object is created and responds as expected.

        """
        content = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod '
                   'tempor incididunt ut labore et dolore magna aliqua.')
        metadata ={'field1': 'Value 1', 'field2': 'Value 2'}
        d = Document(page_content=content, metadata=metadata)
        self.assertEqual(d.page_content, content)
        self.assertEqual(d.metadata, metadata)

    def test01b__object__no_metadata(self):
        """Test the ``Document`` object itself, without metadata.

        :Test:
            - Verify the object is created and responds as expected.

        """
        content = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod '
                   'tempor incididunt ut labore et dolore magna aliqua.')
        metadata ={}
        d = Document(page_content=content)
        self.assertEqual(d.page_content, content)
        self.assertEqual(d.metadata, metadata)
