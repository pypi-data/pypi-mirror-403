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
    from .config.config import SETTINGS
    from .objects.documentobjects import Document
    from ._version import __version__
except ImportError:
    from docp_core.config.config import SETTINGS
    from docp_core.objects.documentobjects import Document
    from docp_core._version import __version__
