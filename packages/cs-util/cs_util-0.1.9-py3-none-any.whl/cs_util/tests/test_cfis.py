"""UNIT TESTS FOR CFIS SUBPACKAGE.

This module contains unit tests for the cfis subpackage.

"""

import os

import numpy as np
from numpy import testing as npt
from astropy import units

from unittest import TestCase

from cs_util import cfis


class CfisTestCase(TestCase):
    """Test case for the ``cfis`` module."""

    def setUp(self):
        """Set test parameter values."""

        self._size_tile = 0.5 * units.deg

        self._tile_number_ok = ["270.283", "188-308"]
        self._nix = ["270", "188"]
        self._niy = ["283", "308"]
        self._dec = [51.5, 64]
        self._ra = [216.86237, 214.43017]
        self._unit = units.deg

        self._nix_nok = ["23x", "1234"]
        self._tile_number_nok = "12x.456"

    def tearDown(self):
        """Unset test parameter values."""
        self._tile_number_ok = None
        self._nix = None
        self._niy = None
        self._dec = None
        self._ra = None
        self._unit = None
        self._tile_number_nok = None

    def test_Cfis(self):
        """Test ``cs_util.Cfis`` class."""
        self.assertTrue(self._size_tile == cfis.Cfis().size["tile"])

    def test_get_tile_number(self):
        """Test ``cs_util.get_tile_number`` method."""

        # Test return values for valid input tile numbers
        for idx, tile_number_ok in enumerate(self._tile_number_ok):
            nix, niy = cfis.get_tile_number(tile_number_ok)
            self.assertTrue(
                (nix == self._nix[idx]) and (niy == self._niy[idx]),
                msg=f"{nix}!={self._nix[idx]} or {niy}!={self._niy[idx]}",
            )

        self.assertRaises(
            ValueError, cfis.get_tile_number, self._tile_number_nok
        )

    def test_get_tile_coord_from_nixy(self):
        """Test ``cs_util.get_tile_coord_from_nixy`` method."""

        # Call with scalar arguments
        for idx in range(len(self._nix)):
            ra, dec = cfis.get_tile_coord_from_nixy(
                self._nix[idx],
                self._niy[idx],
            )

            # Test values
            npt.assert_almost_equal(
                ra.value,
                self._ra[idx],
                err_msg=f"{ra}!={self._ra[idx]}",
                decimal=5,
            )
            npt.assert_almost_equal(
                dec.value,
                self._dec[idx],
                err_msg=f"{dec}!={self._dec[idx]}",
            )

            # Test units
            self.assertTrue(ra.unit == self._unit)
            self.assertTrue(dec.unit == self._unit)

        # Call with list arguments
        ra, dec = cfis.get_tile_coord_from_nixy(self._nix, self._niy)
        for idx in range(len(self._nix)):
            # Test values
            npt.assert_almost_equal(
                ra[idx].value,
                self._ra[idx],
                err_msg=f"{ra[idx]}!={self._ra[idx]}",
                decimal=5,
            )
            npt.assert_almost_equal(
                dec[idx].value,
                self._dec[idx],
                err_msg=f"{dec[idx]}!={self._dec[idx]}",
            )
            # Test units
            self.assertTrue(ra[idx].unit == self._unit)
            self.assertTrue(dec[idx].unit == self._unit)

        # Test exception for invalid input
        self.assertRaises(
            ValueError,
            cfis.get_tile_coord_from_nixy,
            self._nix_nok,
            self._niy,
        )
        self.assertRaises(
            ValueError,
            cfis.get_tile_coord_from_nixy,
            self._niy,
            self._nix_nok,
        )
        self.assertRaises(
            ValueError,
            cfis.get_tile_coord_from_nixy,
            self._nix_nok[0],
            self._niy[0],
        )
