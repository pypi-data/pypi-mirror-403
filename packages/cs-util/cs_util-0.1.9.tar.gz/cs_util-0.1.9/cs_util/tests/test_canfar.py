"""UNIT TESTS FOR CANFAR SUBPACKAGE.

This module contains unit tests for the canfar subpackage.

"""

from unittest import TestCase

from numpy import testing as npt
import os
import sys

from cs_util import canfar


class CanfarTestCase(TestCase):
    """Test case for the ``canfar`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._cmd_ok = "vcp"
        self._cmd_nok = "vxx"

    def tearDown(self):
        """Unset test parameter values."""
        self._cmd_ok = None
        self._cmd_nok = None

    def test_init_vos(self):
        """Test ``cs_util.canfar.vosHandler()`` with
        vos command strings.

        """
        # Test whether command is set
        vos = canfar.vosHandler(self._cmd_ok)
        npt.assert_equal(
            vos.command.__name__,
            self._cmd_ok,
            "vos command not set",
        )

        # Test error for invalid command
        with self.assertRaises(ValueError) as context:
            vos = canfar.vosHandler(self._cmd_nok)
