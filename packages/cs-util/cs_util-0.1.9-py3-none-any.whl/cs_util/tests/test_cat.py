"""UNIT TESTS FOR CAT SUBPACKAGE.

This module contains unit tests for the cat subpackage.

"""

import os

import numpy as np
from numpy import testing as npt

from unittest import TestCase

from cs_util import cat


class CatTestCase(TestCase):
    """Test case for the ``cat`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._primary_header = {}
        self._keys = ["AUTHOR", "SOFTNAME", "SOFTVERS", "DATE"]

        self._keys_matrix = ["R_", "R_g", "R_S"]
        self._keys_c = ["c"]
        self._R = np.array([[0.5, 0.7], [-0.2, 1.2]])
        self._R_shear = np.array([[0.4, 0.6], [-0.1, 1.1]])
        self._R_select = np.array([[0.1, 0.2], [0.0, -0.15]])
        self._c = np.array([-0.001, 2.1e-5])

        self._bin_edges = np.array([0, 1, 1.3])
        self._bin_centers = np.array([0.5, 1.15])

    def tearDown(self):
        """Unset test parameter values."""
        self._primary_header = None
        self._keys_matrix = None
        self._keys_c = None
        self._R = None
        self._R_shear = None
        self._R_select = None
        self._c = None

        self._out_path = None

    def test_write_header_info_sp(self):
        """Test ``cs_util.cat.write_header_info_sp`` method."""
        primary_header = cat.write_header_info_sp(self._primary_header)
        for key in self._keys:
            self.assertTrue(key in primary_header, msg=key)

    def test_add_shear_bias_to_header(self):
        """Test ``cs_util.cat.add_shear_bias_to_header`` method."""
        primary_header = self._primary_header
        cat.add_shear_bias_to_header(
            primary_header, self._R, self._R_shear, self._R_select, self._c
        )

        for key_base in self._keys_matrix:
            if key_base == "R_":
                key = "R"
            else:
                key = key_base
            self.assertTrue(key in primary_header, msg=key)
            for idx in (1, 2):
                for jdx in (1, 2):
                    key = f"{key_base}{idx}{jdx}"
                    self.assertTrue(key in primary_header, msg=key)

            for idx in (1, 2):
                for jdx in (1, 2):
                    key = f"R_{idx}{jdx}"
                    npt.assert_equal(
                        self._R[idx - 1, jdx - 1],
                        primary_header[key][0],
                        f"Incorrect value for {key}",
                    )

    def test_bin_edges2centers(self):
        """Test ``cs_util.cat.bin_edges2centers`` method."""
        bin_centers = cat.bin_edges2centers(self._bin_edges)
        self.assertTrue(all(bin_centers == self._bin_centers))
