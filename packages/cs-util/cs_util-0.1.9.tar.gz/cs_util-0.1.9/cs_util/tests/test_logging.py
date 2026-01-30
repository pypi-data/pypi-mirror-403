"""UNIT TESTS FOR LOGGING SUBPACKAGE.

This module contains unit tests for the logging subpackage.

"""

from unittest import TestCase

from numpy import testing as npt
import os
import sys

from cs_util import logging


class LoggingTestCase(TestCase):
    """Test case for the ``logging`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._argv = [
            "test_cmd arg",
            "-s",
            "opt_short",
            "--long",
            "opt_long",
            "-l",
            '"opt 1 2 list"',
            "-c",
            "opt_special_char[x]",
        ]
        self._log_file_path = "log_test"
        self._log_file_path_default = "log_test_cmd arg"

    def tearDown(self):
        """Unset test parameter values."""
        self._argv = None
        os.remove(self._log_file_path)
        os.remove(self._log_file_path_default)
        self._log_file_path = None

    def test_log_command(self):
        """Test ``cs_util.logging.log_command`` method with
        argument string.

        """
        # Test log file content

        names_output = [self._log_file_path, None]
        names_input = [self._log_file_path, self._log_file_path_default]

        for name_out, name_in in zip(names_output, names_input):
            # Create log command file with no return
            fh_none = logging.log_command(
                self._argv,
                name=name_out,
                close_no_return=True,
            )

            # Read log command file
            with open(name_in, "r") as file:
                log_str = file.read().replace("\n", "")
            os.unlink(name_in)

            # Mask special characters
            argv_list = []
            for a in self._argv:
                if "[" in a or "]" in a:
                    a = f'"{a}"'
                argv_list.append(a)

            # Transform argv list to str
            argv_str = " ".join(argv_list)

            # Test for equality with input
            npt.assert_equal(argv_str, log_str, "Incorrect log file output")

            # Test return type ``None``
            npt.assert_equal(fh_none, None, "Incorrect return type")

        # Test return type is file handler: read and test type string
        # Create log command file with no return
        fh_open = logging.log_command(
            self._argv,
            name=self._log_file_path,
            close_no_return=False,
        )
        self.assertIsNotNone(fh_open, msg="Incorrect return object")

        # Test return object is stdout
        fh_stdout = logging.log_command(
            self._argv,
            name="sys.stdout",
            close_no_return=False,
        )
        npt.assert_equal(fh_stdout, sys.stdout, "Incorrect return object")

        # Test return object is stderr
        fh_stderr = logging.log_command(
            self._argv,
            name="sys.stderr",
            close_no_return=False,
        )
        npt.assert_equal(fh_stderr, sys.stderr, "Incorrect return object")

        # Test logging with default log file name
        fh_none = logging.log_command(
            self._argv,
            close_no_return=True,
        )
