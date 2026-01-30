"""UNIT TESTS FOR COSMO SUBPACKAGE.

This module contains unit tests for the cosmo subpackage.

"""

import os
import pickle

from numpy import testing as npt
import numpy as np

from astropy import units
import pyccl as ccl

from unittest import TestCase

from cs_util import cosmo


class CosmoTestCase(TestCase):
    """Test case for the ``cosmo`` module."""

    def setUp(self):
        """Set test parameter values."""
        self._z_source = 0.8
        self._z_lens = 0.5
        self._z_source_arr = [0.4, 0.6, 0.8, 0.9]
        self._nz_source_arr = [0.5, 0.6, 2.2, 1.6]
        self._cosmo = ccl.CosmologyVanillaLCDM()
        self._sigma_crit_value = 3920.1478
        # Value verified with package dsigma as 3919.700

        self._sigma_crit_value_eff = 3917.2681
        self._sigma_crit_value_eff_m1 = 0.0002267

        self._sigma_crit_unit = units.Msun / units.pc**2
        self._d_source = 1617.9195 * units.Mpc
        self._d_lens = 1315.3937 * units.Mpc

        self._d_source_arr = [
            1157.82363726,
            1440.63922894,
            1617.91952285,
            1678.82870081,
        ] * units.Mpc

        self._cos_def = cosmo = ccl.Cosmology(
            Omega_c=0.27,
            Omega_b=0.045,
            h=0.67,
            sigma8=0.83,
            n_s=0.96,
        )

        self._theta = [1, 10, 100] * units.arcmin
        self._z = np.linspace(0.2, 1.2, 50)
        self._nz = (self._z / 0.8) ** 2 * np.exp(-((self._z / 0.8) ** 1.5))
        self._xip = [1.33045991e-04, 2.13181640e-05, 2.13598131e-06]
        self._xim = [1.97627462e-05, 1.23127046e-05, 2.17498675e-06]

    def tearDown(self):
        """Unset test parameter values."""
        self._z_source = None
        self._z_lens = None
        self._cosmo = None
        self._sigma_crit_value = None
        self._sigma_crit_unit = None
        self._d_source = None
        self._d_lens = None
        self._ds_cosmo = None
        self._cos_def = None
        self._theta = None
        self._z = None
        self._nz = None
        self._xip = None
        self._xim = None

    def test_sigma_crit(self):
        """Test ``cs_util.cosmo.sigma_crit`` method."""
        sigma_crit = cosmo.sigma_crit(
            self._z_lens,
            self._z_source,
            self._cosmo,
        )
        # Test return value
        npt.assert_almost_equal(
            sigma_crit.value,
            self._sigma_crit_value,
            decimal=3,
        )
        # Test return unit
        npt.assert_equal(sigma_crit.unit, self._sigma_crit_unit)

        # Test with lens behind source
        sigma_crit = cosmo.sigma_crit(
            self._z_lens, self._z_lens / 2, self._cosmo
        )
        npt.assert_equal(sigma_crit, 0 * self._sigma_crit_unit)

        # Test changing default arguments
        sigma_crit = cosmo.sigma_crit(
            self._z_lens,
            self._z_source,
            self._cosmo,
            d_source=self._d_source,
        )
        npt.assert_almost_equal(
            sigma_crit.value,
            self._sigma_crit_value,
            decimal=2,
        )

        sigma_crit = cosmo.sigma_crit(
            self._z_lens,
            self._z_source,
            self._cosmo,
            d_lens=self._d_lens,
        )
        npt.assert_almost_equal(
            sigma_crit.value,
            self._sigma_crit_value,
            decimal=2,
        )

        sigma_crit = cosmo.sigma_crit(
            self._z_lens,
            self._z_source,
            self._cosmo,
            d_lens=self._d_lens,
            d_source=self._d_source,
        )
        npt.assert_almost_equal(
            sigma_crit.value,
            self._sigma_crit_value,
            decimal=2,
        )

    def test_sigma_crit_eff(self):
        """Test ``cs_util.cosmo.sigma_crit_eff`` method."""
        sigma_crit_eff = cosmo.sigma_crit_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
        )
        # Test return value
        npt.assert_almost_equal(
            sigma_crit_eff.value,
            self._sigma_crit_value_eff,
            decimal=3,
        )

        # Test return unit
        npt.assert_equal(sigma_crit_eff.unit, self._sigma_crit_unit)

        # Test exception
        self.assertRaises(
            IndexError,
            cosmo.sigma_crit_eff,
            self._z_lens,
            self._z_source_arr[:-1],
            self._nz_source_arr,
            self._cosmo,
        )

        # Test changing default arguments
        sigma_crit_eff = cosmo.sigma_crit_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_source_arr=self._d_source_arr,
        )
        npt.assert_almost_equal(
            sigma_crit_eff.value,
            self._sigma_crit_value_eff,
            decimal=3,
        )
        sigma_crit_eff = cosmo.sigma_crit_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_lens=self._d_lens,
        )
        npt.assert_almost_equal(
            sigma_crit_eff.value,
            self._sigma_crit_value_eff,
            decimal=3,
        )
        sigma_crit_eff = cosmo.sigma_crit_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_lens=self._d_lens,
            d_source_arr=self._d_source_arr,
        )
        npt.assert_almost_equal(
            sigma_crit_eff.value,
            self._sigma_crit_value_eff,
            decimal=3,
        )

    def test_sigma_crit_m1_eff(self):
        """Test ``cs_util.cosmo.sigma_crit_m1_eff`` method."""
        sigma_crit_m1_eff = cosmo.sigma_crit_m1_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
        )
        # Test return value
        npt.assert_almost_equal(
            sigma_crit_m1_eff.value,
            self._sigma_crit_value_eff_m1,
            decimal=4,
        )
        # Test return unit
        npt.assert_equal(
            sigma_crit_m1_eff.unit, (1 / self._sigma_crit_unit).unit
        )

        # Test exception when redshift array lengths inconsistent
        self.assertRaises(
            IndexError,
            cosmo.sigma_crit_m1_eff,
            self._z_lens,
            self._z_source_arr[:-1],
            self._nz_source_arr,
            self._cosmo,
        )

        # Test changing default arguments
        sigma_crit_m1_eff = cosmo.sigma_crit_m1_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_source_arr=self._d_source_arr,
        )
        npt.assert_almost_equal(
            sigma_crit_m1_eff.value,
            self._sigma_crit_value_eff_m1,
            decimal=3,
        )
        sigma_crit_m1_eff = cosmo.sigma_crit_m1_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_lens=self._d_lens,
        )
        npt.assert_almost_equal(
            sigma_crit_m1_eff.value,
            self._sigma_crit_value_eff_m1,
            decimal=3,
        )
        sigma_crit_m1_eff = cosmo.sigma_crit_m1_eff(
            self._z_lens,
            self._z_source_arr,
            self._nz_source_arr,
            self._cosmo,
            d_lens=self._d_lens,
            d_source_arr=self._d_source_arr,
        )
        npt.assert_almost_equal(
            sigma_crit_m1_eff.value,
            self._sigma_crit_value_eff_m1,
            decimal=3,
        )

    def test_get_cosmo_default(self):
        """Test ``cs_util.get_cosmo_default`` method."""

        cos_def = cosmo.get_cosmo_default()

        npt.assert_equal(pickle.dumps(cos_def), pickle.dumps(self._cos_def))

    def test_xipm_theo(self):
        xip, xim = cosmo.xipm_theo(
            self._theta,
            self._cosmo,
            self._z,
            self._nz,
        )
        npt.assert_equal(len(xip), len(self._theta))
        for idx in range(len(self._theta)):
            npt.assert_almost_equal(xip[idx], self._xip[idx], decimal=4)
            npt.assert_almost_equal(xim[idx], self._xim[idx], decimal=4)
