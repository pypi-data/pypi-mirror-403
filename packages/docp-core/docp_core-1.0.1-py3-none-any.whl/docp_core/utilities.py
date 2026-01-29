#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides utility-based functionality for the
            project.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

import os
import re
from glob import glob
from utils4 import futils


class Utilities:
    """General (cross-project) utility functions."""

    @staticmethod
    def build_project_outpath(subpath: str) -> str:
        """Build (and create) the path for project output files.

        Args:
            subpath (str): The sub-path to be appended to the default
            ``~/Desktop/docp`` path.

        If the path does not exist, it will be created automatically.

        Returns:
            str: The full path as a string.

        """
        base = os.path.join(os.path.expanduser('~/Desktop'), 'docp')
        path = os.path.join(base, subpath)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def collect_files(path: str, ext: str='**', recursive: bool=False) -> list:
        """Collect all files for a given extension from a path.

        Args:
            path (str): Full path serving as the root for the search.
            ext (str, optional): If the ``path`` argument refers to a
                *directory*, a specific file extension can be specified
                here. For example: ``ext = 'pdf'``.

                If anything other than ``'**'`` is provided, all
                alpha-characters are parsed from the string, and prefixed
                with ``*.``. Meaning, if ``'.pdf'`` is passed, the
                characters ``'pdf'`` are parsed and prefixed with ``*.``
                to create ``'*.pdf'``. However, if ``'things.foo'`` is
                passed, the derived extension will be ``'*.thingsfoo'``.
                Defaults to '**', for an 'everything' or recursive search
                (if the ``resursive`` argument is passed as True).

            recursive (bool, optional): Instruct the search to recurse
                into sub-directories. Defaults to False.

        Returns:
            list: The list of full file paths returned by the ``glob``
            call. Any directory-only paths are removed.

        """
        if ext != '**':
            ext = f'*.{re.findall("[a-zA-Z]+", ext)[0]}'
        return list(filter(os.path.isfile, glob(os.path.join(path, ext), recursive=recursive)))

    @staticmethod
    def ispdf(path: str) -> bool:
        """Test the file signature. Verify this is a valid PDF file.

        Args:
            path (str): Path to the file being tested.

        Returns:
            bool: True if this is a valid PDF file, otherwise False.

        """
        return futils.ispdf(path)

    @staticmethod
    def iszip(path: str) -> bool:
        """Test the file signature. Verify this is a valid ZIP archive.

        Args:
            path (str): Path to the file being tested.

        Returns:
            bool: True if this is a valid ZIP archive, otherwise False.

        """
        return futils.iszip(path)

    @staticmethod
    def parse_to_keywords(resp: str) -> str:
        r"""Parse the bot's response into a list of keywords.

        Args:
            resp (str): Text response directly from the bot.

        The bullet points extracted must be in any of the following
        forms.

        Asterisk as bullet points:

            - * Spam
            - * Eggs

        Hyphen as bullet points:

            - - Spam
            - - Eggs

        Numbered (1):

            - 1. Spam
            - 2. Eggs

        Numbered (2):

            - 1\) Spam
            - 2\) Eggs

        Returns:
            str: A comma separated string of keywords extracted from the
            response, *converted to lower case*.

        """
        # Capture asterisk bullet points or a numbered list.
        rexp = re.compile(r'(?:-|\*|[0-9]+[\.\)])\s*(.*)\n?')
        trans = {47: ' '}
        resp_ = resp.translate(trans).lower()
        kwds = rexp.findall(resp_)
        if kwds:
            return ', '.join(kwds)
        return ''

    @staticmethod
    def remove_duplicate_lines(text: str) -> str:
        """Remove any duplicated lines from the document.

        Generally, this function will be used to remove repeated headers
        and footers from a document.

        Args:
            text (str): A string containing text from which duplicated
                lines are to be removed.

        Returns:
            str: A string containing only the unique lines (or empty
            lines) from the provided text.

        """
        tmp = []
        lines = filter(None, re.split('(\n+)', text))  # re.split keeps the separator.
        # Set comprehension cannot be used here as order *must* be retained.
        for line in lines:
            # Keep only unique lines and preserve newline characters.
            if line not in tmp or '\n' in line:
                tmp.append(line)
        return ''.join(tmp)


utilities = Utilities()
