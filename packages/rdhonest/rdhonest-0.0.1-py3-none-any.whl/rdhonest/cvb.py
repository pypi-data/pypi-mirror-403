"""
Critical values for CIs based on a biased Gaussian estimator.
"""

import numpy as np
from scipy import stats


def cvb(B, alpha: float = 0.05):
    """
    Critical values for CIs based on a biased Gaussian estimator.

    Computes the critical value cv_{1-alpha}(B) such that the confidence
    interval X +/- cv_{1-alpha}(B) has coverage 1-alpha, where the estimator
    X is normally distributed with variance equal to 1 and maximum bias
    at most B.

    Parameters
    ----------
    B : float or array-like
        Maximum bias, vector of non-negative numbers.
    alpha : float
        Determines CI level, 1-alpha. Scalar between 0 and 1.

    Returns
    -------
    np.ndarray
        Vector of critical values, one for each value of maximum bias.

    Examples
    --------
    >>> cvb(1, alpha=0.1)  # 90% critical value
    >>> cvb(0)  # Usual 95% critical value
    >>> cvb([0, 0.5, 1], alpha=0.05)  # Returns 3 critical values
    """
    B = np.atleast_1d(B).astype(float)
    cv = np.empty_like(B)

    for i, b in enumerate(B):
        if np.isnan(b):
            cv[i] = np.nan
        elif b < 0 or alpha <= 0 or alpha >= 1:
            raise ValueError("B must be >= 0 and 0 < alpha < 1")
        elif b < 10:
            # Use non-central chi-squared distribution
            cv[i] = np.sqrt(stats.ncx2.ppf(1 - alpha, df=1, nc=b**2))
        else:
            # For large B, use normal approximation
            cv[i] = b + stats.norm.ppf(1 - alpha)

    return cv if len(cv) > 1 else cv[0]


def fill_coefs(co: dict) -> dict:
    """
    Fill in confidence interval coefficients.

    Parameters
    ----------
    co : dict
        Coefficient dictionary with estimate, std.error, maximum.bias, alpha.

    Returns
    -------
    dict
        Updated dictionary with confidence interval endpoints.
    """
    B = co['maximum.bias'] / co['std.error']
    cv = cvb(B, co['alpha'])

    co['conf.low'] = co['estimate'] - cv * co['std.error']
    co['conf.high'] = co['estimate'] + cv * co['std.error']
    co['conf.low.onesided'] = co['estimate'] - (B + stats.norm.ppf(1 - co['alpha'])) * co['std.error']
    co['conf.high.onesided'] = co['estimate'] + (B + stats.norm.ppf(1 - co['alpha'])) * co['std.error']
    co['cv'] = cv
    co['p.value'] = (stats.norm.cdf(B - abs(co['estimate'] / co['std.error'])) +
                     stats.norm.cdf(-B - abs(co['estimate'] / co['std.error'])))

    return co
