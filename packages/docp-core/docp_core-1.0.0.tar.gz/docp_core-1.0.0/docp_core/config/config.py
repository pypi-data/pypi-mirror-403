#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the configuration items for the docp
            project.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

import os
import tomllib


class Config:
    """General project-based configuration controller class."""

    def __init__(self) -> None:
        """Config class initialiser."""
        self._cfg = None
        self._load_config()

    @property
    def config(self) -> dict:
        """Accessor to the configuration values."""
        return self._cfg

    def _load_config(self) -> None:
        """Load the config file into memory."""
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.toml')
        with open(path, 'rb') as f:
            self._cfg = tomllib.load(f)


SETTINGS = Config().config
