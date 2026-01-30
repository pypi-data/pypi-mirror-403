"""UNIT TESTS FOR PLOTS SUBPACKAGE.

This module contains unit tests for the plots subpackage.

"""

import os

import numpy as np
from matplotlib.figure import Figure
from numpy import testing as npt

from unittest import TestCase

from cs_util import plots


class PlotsTestCase(TestCase):
    """Test case for the ``plots`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._fig_size = [13, 7]

        self._x = [1, 1.5, 2, 2, 3, 5]
        self._n_bin = 4
        self._x_range = [1, 5]
        self._img_path = "test.png"
        self._n_arr = np.array([2.0, 2.0, 1.0, 1.0])
        self._bins = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    def tearDown(self):
        """Unset test parameter values."""
        self._fig_size = None
        self._x = None
        self._n_bin = None
        self._x_range = None

        if os.path.exists(self._img_path):
            os.remove(self._img_path)
        self._img_path = None

        self._n_arr = None
        self._bins = None

    def test_figure(self):
        """Test ``cs_util.weighted_avg_and_std`` method."""
        fig = plots.figure(figsize=(self._fig_size[0], self._fig_size[1]))

        # Check for return value
        self.assertIsNotNone(fig, msg="Incorrect return type")

        # Check image size
        size = fig.get_size_inches()
        for idx in (0, 1):
            npt.assert_almost_equal(size[idx], self._fig_size[idx])

    def test_plot_histograms(self):
        """Test ``cs_util.plot_histograms`` method."""
        vline_x_arr = [None, [1.2]]
        vline_lab_arr = [None, ["vlab"]]
        for vline_x, vline_lab in zip(vline_x_arr, vline_lab_arr):
            n_arr, bins = plots.plot_histograms(
                [self._x],
                ["hist 1"],
                "title",
                "$x$",
                "freq",
                self._x_range,
                self._n_bin,
                self._img_path,
                density=False,
                vline_x=vline_x,
                vline_lab=vline_lab,
            )

            # Check return histogram data
            npt.assert_almost_equal(n_arr[0], self._n_arr)
            npt.assert_almost_equal(bins[0], self._bins)

            # Check output plot file
            self.assertTrue(os.path.exists(self._img_path))
