"""CALC.

:Name: calc.py

:Description: This file contains methods for general calculations
              and statistics.

:Author: Martin Kilbinger <martin.kilbinger@cea.fr>

"""

import numpy as np


def weighted_avg_and_std(values, weights, corrected=False):
    """Weighted Avg And Std.

    Weighted average and weighted standard deviation of a sample.

    Parameters
    ----------
    values : array-like
        sample values
    weight : array-like
        weights
    corrected : bool, optional
        Apply Bessel's corrected to the standard deviation
        (division by n-1 instead of n) if ``True``; default is ``False``

    Returns
    -------
    tuple :
        weighted average and weighted standard deviation

    """
    average = np.average(values, weights=weights)

    # Fast and numerically precise:
    variance = np.average((values - average) ** 2, weights=weights)

    if corrected:
        n = len(values)
        variance = variance * n / (n - 1)

    return average, np.sqrt(variance)


def transform_nan(value):
    """Transform Nan.

    Transform a ``nan`` to a very large number.

    Parameters
    ----------
    value : float
        input value

    Returns
    -------
    float
        output value

    """
    large = 1e30

    if np.isnan(value) or np.isinf(value):
        res = 1e30
    else:
        res = value

    return res
