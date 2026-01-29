#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:Purpose:   Testing module for the ``libs.startup`` module.

:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""
# pylint: disable=import-error

import contextlib
import io
try:
    from .base import TestBase
    from .testlibs.testutils import testutils
except ImportError:
    from base import TestBase
    from testlibs.testutils import testutils
# The imports for docp_* must be after TestBase.
from docp_docling.libs.startup import Startup


class TestStartup(TestBase):
    """Testing class used to test the ``libs.startup`` module."""

    @classmethod
    def setUpClass(cls):
        """Run this logic at the start of all test cases."""
        testutils.msgs.startoftest(msg='libs.startup')

    def test01a__run(self):
        """Test the ``run`` method.

        :Test:
            - Verify the method returns True to show a complete setup.

        """
        s = Startup()
        tst = s.run()
        self.assertTrue(tst)

    def test02a___alert__model_path_not_populated(self):
        """Test the ``_alert__model_path_not_populated`` method.

        :Test:
            - Hack the SETTINGS to remove the model path and trigger a
              warning showing the config key must be updated.

        """
        # pylint: disable=import-outside-toplevel  # OK for this test
        from docp_core import SETTINGS
        # Backup the path.
        _path = SETTINGS['paths']['models']['docling']
        # Override the path for testing.
        SETTINGS['paths']['models']['docling'] = '<EMPTY>'
        buff = io.StringIO()
        with contextlib.redirect_stdout(buff):
            s = Startup()
            tst1 = s.run()
            tst2 = buff.getvalue()
        self.assertFalse(tst1)
        self.assertIn('[WARNING]:', tst2)
        self.assertIn('config key must be populated', tst2)
        # Restore the path for future tests.
        SETTINGS['paths']['models']['docling'] = _path
