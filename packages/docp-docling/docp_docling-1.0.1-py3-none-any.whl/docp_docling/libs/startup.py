#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module contains startup tasks which are run by the
            library's ``__init__`` file.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

from utils4.user_interface import ui
from docp_core import SETTINGS


class Startup:
    """Library startup routines wrapper class."""

    def __init__(self) -> None:
        """Library startup class initialiser."""
        self._results = []

    def run(self) -> bool:
        """Run all library start-up tasks.

        Returns:
            bool: True if all startup tasks succeed. Otherwise, False.

        """
        self._alert__model_path_not_populated()
        return all(self._results)

    def _alert__model_path_not_populated(self) -> None:
        """Alert the user if the following keys are not populated.

        Keys:
            - models.paths.docling

        """
        keys = ('docling', )
        for key in keys:
            if SETTINGS['paths']['models'].get(key) == "<EMPTY>":
                ui.print_warning((f'[WARNING]: The following config key must be populated: {key}\n'
                                  '-- Update required in: docp-core/config/config.toml'))
                self._results.append(False)
