"""COSMO.

:Name: cosmo.py

:Description: This file contains methods for cosmological
              quantities.

:Author: Martin Kilbinger <martin.kilbinger@cea.fr>

"""

import numpy as np

from astropy import constants
from astropy import units

import pyccl as ccl


def get_cosmo_default():
    """Get Cosmo Default.

    Return default cosmology.

    Returns
    -------
    Cosmology
        pyccl cosmology object

    """
    cos = ccl.Cosmology(
        Omega_c=0.27,
        Omega_b=0.045,
        h=0.67,
        sigma8=0.83,
        n_s=0.96,
    )

    # Set ell_max to large value, for spline interpolation (in integral over
    # C _ell to get real-space correlation functions). Avoid aliasing
    # ( oscillations)
    cos.cosmo.spline_params.ELL_MAX_CORR = 10_000_000
    cos.cosmo.spline_params.N_ELL_CORR = 5_000

    return cos


def sigma_crit(z_lens, z_source, cos, d_lens=None, d_source=None):
    """Sigma Crit.

    Critical surface mass density.

    Parameters
    ----------
    z_lens : float
        lens redshift
    z_source : float
        source redshift
    cos : pyccl.core.Cosmology
        cosmological parameters
    d_lens : astropy.units.Quantity, optional
        precomputed anguar diameter distance to lens, computed from z_lens
        if ``None`` (default)
    d_source : astropy.units.Quantity, optional
        precomputed anguar diameter distance to sourcce, computed from z_source
        if ``None`` (default)

    Returns
    -------
    astropy.units.Quantity
        critical surface mass density with units of M_sol / pc^2

    """
    unit_return = units.Msun / units.pc**2

    # Return 0 if lens behind source
    if z_lens >= z_source:
        return 0.0 * unit_return

    a_lens = 1 / (1 + z_lens)
    a_source = 1 / (1 + z_source)
    if d_lens is None:
        d_lens = cos.angular_diameter_distance(a_lens) * units.Mpc
    if d_source is None:
        d_source = cos.angular_diameter_distance(a_source) * units.Mpc

    d_lens_source = cos.angular_diameter_distance(a_lens, a_source) * units.Mpc

    frac = d_source / (d_lens_source * d_lens)
    pref = constants.c**2 / (4 * np.pi * constants.G)

    sigma_cr = (pref * frac).to(unit_return)

    return sigma_cr


def sigma_crit_eff(
    z_lens,
    z_source_arr,
    nz_source_arr,
    cos,
    d_lens=None,
    d_source_arr=None,
):
    """Sigma Crit Eff.

    Effective critical surface mass density, which
    is sigma_crit(z_lens, z_source) weighted by nz_source.

    Parameters
    ----------
    z_lens : float
        lens redshift
    z_source_arr : list
        source redshifts
    nz_source_arr : list
        number of galaxies at z_source
    cos : pyccl.core.Cosmology
        cosmological parameters
    d_lens : astropy.units.Quantity, optional
        precomputed anguar diameter distance to lens;
        computed from z_lens if ``None`` (default)
    d_source_arr : list, optional
        precompuated angular diameter distances to sources;
        computed from z_source_arr if ``None`` (default);
        needs to be list of astropy.units.Quantity

    Raises
    ------
    IndexError
        If lists ``z_source_arr``, ``nz_source_arr``, and d_source_arr
        do not match

    Returns
    -------
    astropy.units.Quantity
        effective critical surface mass density with units of M_sol / pc^2

    """
    n_source = len(z_source_arr)

    if d_source_arr is None:
        d_source_arr = [None] * n_source

    if (len(nz_source_arr) != n_source) or (len(d_source_arr) != n_source):
        raise IndexError(
            "Lists for source z, n(z), and/or d_ang have different lenghts"
        )

    sigma_cr_arr = []
    for idx in range(n_source):
        sigma_cr = sigma_crit(
            z_lens,
            z_source_arr[idx],
            cos,
            d_lens=d_lens,
            d_source=d_source_arr[idx],
        )

        # Get unit
        if len(sigma_cr_arr) == 0:
            unit = sigma_cr.unit

        sigma_cr_arr.append(sigma_cr.value)

    # Mean sigma_cr weighted by source redshifts.
    # np.average can only deal with unitless quantities.
    sigma_cr_eff = np.average(sigma_cr_arr, weights=nz_source_arr)

    return sigma_cr_eff * unit


def sigma_crit_m1_eff(
    z_lens,
    z_source_arr,
    nz_source_arr,
    cos,
    d_lens=None,
    d_source_arr=None,
):
    """Sigma Crit M1 Eff.

    Effective inverse critical surface mass density, which
    is sigma_crit^{-1}(z_lens, z_source) weighted by nz_source.
    See Eq. (17) in :cite:`2004AJ....127.2544S`.

    Parameters
    ----------
    z_lens : float
        lens redshift
    z_source_arr : list
        source redshifts
    nz_source_arr : list
        number of galaxies at z_source
    cos : pyccl.core.Cosmology
        cosmological parameters
    d_lens : astropy.units.Quantity, optional
        precomputed anguar diameter distance to lens;
        computed from z_lens if ``None`` (default)
    d_source_arr : float, optional
        precomputed anguar diameter distance to sources;
        computed from z_source_arr if ``None`` (default);
        needs to be list of astropy.units.Quantity

    Raises
    ------
    IndexError
        If lists ``z_source_arr``, ``nz_source_arr``, and ``d_source_arr``
        do not match

    Returns
    -------
    astropy.units.Quantity
        effective inverse critical surface mass density with units of
        M_sol / pc^2

    """
    n_source = len(z_source_arr)

    if d_source_arr is None:
        d_source_arr = [None] * n_source

    if (len(nz_source_arr) != n_source) or (len(d_source_arr) != n_source):
        raise IndexError(
            "Lists for source z, n(z), and/or d_ang have different lenghts"
        )

    sigma_cr_m1_arr = []
    weights = []

    for idx in range(n_source):
        sigma_cr = sigma_crit(
            z_lens,
            z_source_arr[idx],
            cos,
            d_lens=d_lens,
            d_source=d_source_arr[idx],
        )

        # Get unit
        if len(sigma_cr_m1_arr) == 0:
            unit = 1 / sigma_cr.unit

        # If lens behind source: continue
        if sigma_cr == 0:
            continue

        sigma_cr_m1 = 1 / sigma_cr

        sigma_cr_m1_arr.append(sigma_cr_m1.value)
        weights.append(nz_source_arr[idx])

    sigma_cr_m1_eff = np.average(sigma_cr_m1_arr, weights=weights)

    return sigma_cr_m1_eff * unit


def xipm_theo(
    theta,
    cos,
    z,
    dndz,
):
    """Xipm Theo.

    Return theoretical prediction of the shear two-point correlation function.

    Parameters
    ----------
    theta : list
        angular scales, list of type astropy.units.Quantity
    cos : pyccl.core.Cosmology
        cosmological parameters
    z : list
        redshift centers
    dndz : list
        number of galaxies for each z (arbitrary normalisation)

    Returns
    -------
    numpy.ndarray
        xi_+
    numpy.ndarray
        xi_-

    """
    # Create objects to represent tracers of the weak lensing signal with this
    # number density (with has_intrinsic_alignment=False)
    lens_tr = ccl.WeakLensingTracer(cos, dndz=(z, dndz))

    # Calculate the angular cross-spectrum of the two tracers as a function
    # of ell
    # MKDEBUG TODO: vary, use unions-shear-ustc-cea/unions_wl/defaults.py
    ell = np.logspace(0, np.log10(10000), 1000)
    cl = ccl.angular_cl(cos, lens_tr, lens_tr, ell)

    method = "Bessel"

    xipm = {}
    for corr_type in ("GG+", "GG-"):
        xipm[corr_type] = ccl.correlation(
            cos,
            ell=ell,
            C_ell=cl,
            theta=theta.to("deg"),
            type=corr_type,
        )

    return xipm["GG+"], xipm["GG-"]
