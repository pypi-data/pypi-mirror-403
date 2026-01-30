"""UNIT TESTS FOR ARGS SUBPACKAGE.

This module contains unit tests for the args subpackage.

"""

import os

import numpy as np
from numpy import testing as npt
import optparse
import pytest

from unittest import TestCase
from unittest.mock import patch

from cs_util import args


class ArgsTestCase(TestCase):
    """Test case for the ``args`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._params_def = {
            "p_int": 1,
            "p_float": 0.612,
            "p_str": "some_string",
            "p_bool": -1,
            "p_Bool": -1,
            "p_str_def": "second_string",
            "p_none": "",
        }
        self._types = {
            "p_int": "int",
            "p_float": "float",
            "p_bool": "bool",
            "p_Bool": "bool",
            "p_str": "str",
        }
        self._short_options = {
            "p_int": "-i",
            "p_float": "-f",
            "p_bool": "-b",
            "p_Bool": "-B",
            "p_str": "-s",
        }
        self._help_strings = {
            "p_int": "integer option, default={}",
            "p_float": "float option, default={}",
            "p_bool": "bool option, set to True if given",
            "p_Bool": "bool option, set to True if given",
            "p_str": "string option, default={}",
        }
        self._string0 = None
        self._string1 = "abc"
        self._string3 = "a b c"

    def tearDown(self):
        """Unset test parameter values."""
        self._params_def = None
        self._types = None
        self._short_options = None
        self._help_strings = None
        self._string1 = None

    def test_parse_options(self):
        """Test `cs_util.args.parse_options` method."""
        self._options = args.parse_options(
            self._params_def,
            self._short_options,
            self._types,
            self._help_strings,
            args=["-i", "2", "-s", "test", "-b"],
        )

        # Test updated options
        npt.assert_equal(self._options["p_int"], 2)
        npt.assert_equal(self._options["p_str"], "test")
        npt.assert_equal(self._options["p_bool"], True)

        # Test unchanged (default) options
        npt.assert_equal(self._options["p_float"], 0.612)
        npt.assert_equal(self._options["p_Bool"], False)
        npt.assert_equal(self._options["p_str_def"], "second_string")

        # Test default args array
        test_argv = [None, "-i", "2"]
        with patch("sys.argv", test_argv):
            self._options = args.parse_options(
                self._params_def,
                self._short_options,
                self._types,
                self._help_strings,
                args=None,
            )
            npt.assert_equal(self._options["p_int"], 2)

    def test_my_string_split(self):
        """Test `cs_util.args.my_string_split` method."""

        # Test string=None
        results = args.my_string_split(self._string0)
        self.assertIsNone(results)

        # Test string without separator
        results = args.my_string_split(self._string1)
        npt.assert_equal(len(results), 1)
        npt.assert_equal(results[0], self._string1)

        # Test string with separators
        results = args.my_string_split(self._string3)
        npt.assert_equal(len(results), 3)
        for idx in (0, 1, 2):
            npt.assert_equal(results[idx], self._string3[idx * 2])

        # Test different separator
        results = args.my_string_split(self._string3, sep="_")
        npt.assert_equal(len(results), 1)
        npt.assert_equal(results[0], self._string3)

        # Test mismatching number of substrings
        # Exception for stop=True
        with self.assertRaises(ValueError):
            args.my_string_split(self._string3, num=2, stop=True)
        # Return value when stop is False
        results = args.my_string_split(self._string3, num=2, stop=False)
        npt.assert_equal(len(results), 3)
        for idx in (0, 1, 2):
            npt.assert_equal(results[idx], self._string3[idx * 2])
