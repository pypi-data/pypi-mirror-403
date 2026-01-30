"""UNIT TESTS FOR CALC SUBPACKAGE.

This module contains unit tests for the calc subpackage.

"""

import os

import numpy as np
from numpy import testing as npt

from unittest import TestCase

from cs_util import calc


class CatTestCase(TestCase):
    """Test case for the ``cat`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._x = np.array([1, 2, 3, 2, 4, 0.5, 1, 2, 3])
        self._w = np.array([1, 0.5, 0.8, 0.9, 1.2, 1.5, 2, 3, 1.2])
        self._mean_w = 1.929752067
        self._std_w_uncor = 1.041109121
        self._std_w_cor = 1.104262979

    def tearDown(self):
        """Unset test parameter values."""
        self._x = None
        self._w = None

    def test_weighted_avg_and_std(self):
        """Test ``cs_util.calc.weighted_avg_and_std`` method."""
        mean_w, std_w_uncor = calc.weighted_avg_and_std(self._x, self._w)
        npt.assert_almost_equal(
            mean_w, self._mean_w, err_msg="weighted means differ"
        )
        npt.assert_almost_equal(
            std_w_uncor,
            self._std_w_uncor,
            err_msg="uncorrected weighted std differ",
        )

        mean_w, std_w_cor = calc.weighted_avg_and_std(
            self._x, self._w, corrected=True
        )
        npt.assert_almost_equal(
            mean_w, self._mean_w, err_msg="weighted means differ"
        )
        npt.assert_almost_equal(
            std_w_cor,
            self._std_w_cor,
            err_msg="corrected weighted std differ",
        )
