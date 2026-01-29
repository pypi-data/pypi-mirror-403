#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the project initilisation logic.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

# Verify the config is populated before attempting imports.
from utils4.user_interface import ui
try:
    from .libs.startup import Startup
except ImportError:
    from docp_docling.libs.startup import Startup

if not Startup().run():
    # HACK: Raising an error causes document build to fail on docp-loaders.
    #raise RuntimeError('[ERROR]: Startup procedures failed. Check error messages.')
    ui.print_alert('[ERROR]: Startup procedures failed. Check error messages.')

# locals
try:
    from .libs._version import __version__
    from .parsers.pdfparser import PDFParser
except ImportError:
    from docp_docling.libs._version import __version__
    from docp_docling.parsers.pdfparser import PDFParser

