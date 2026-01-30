"""
Smoothness bound estimation for RDHonest.
"""

import numpy as np
from scipy import stats
from typing import Optional, Dict
import pandas as pd

from .utils import RDResults, find_zero
from .cvb import cvb
from .variance import prelim_var


def rd_smoothness_bound(
    obj: RDResults,
    s: int,
    separate: bool = False,
    multiple: bool = True,
    alpha: float = 0.05,
    sclass: str = "H"
) -> pd.DataFrame:
    """
    Lower bound on smoothness constant M in sharp RD designs.

    Estimate a lower bound on the smoothness constant M and provide a lower
    confidence interval for it.

    Parameters
    ----------
    obj : RDResults
        Result of a call to rd_honest.
    s : int
        Number of support points that curvature estimates should average over.
    separate : bool
        If True, report estimates separately above/below cutoff.
    multiple : bool
        If True, use multiple curvature estimates.
    alpha : float
        Confidence level 1-alpha.
    sclass : str
        Smoothness class: "T" for Taylor or "H" for Holder.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'estimate' and 'conf.low' columns.
    """
    d = prelim_var(obj.data, se_initial="EHW")
    X = d.X.flatten()
    Y = d.Y.flatten() if d.Y.ndim == 1 else d.Y[:, 0]

    def dk(Y, X, xu, s2, j):
        """Curvature estimate based on jth set of three points closest to zero."""
        # Indices for three intervals
        I1 = (X >= xu[3*j*s - 3*s]) & (X <= xu[3*j*s - 2*s - 1])
        I2 = (X >= xu[3*j*s - 2*s]) & (X <= xu[3*j*s - s - 1])
        I3 = (X >= xu[3*j*s - s]) & (X <= xu[3*j*s - 1])

        if not (np.any(I1) and np.any(I2) and np.any(I3)):
            return np.array([np.nan] * 11)

        mean_X1, mean_X2, mean_X3 = np.mean(X[I1]), np.mean(X[I2]), np.mean(X[I3])
        mean_Y1, mean_Y2, mean_Y3 = np.mean(Y[I1]), np.mean(Y[I2]), np.mean(Y[I3])

        lam = (mean_X3 - mean_X2) / (mean_X3 - mean_X1)

        if sclass == "T":
            den = (1 - lam) * np.mean(X[I3]**2) + lam * np.mean(X[I1]**2) + np.mean(X[I2]**2)
        else:  # Holder
            den = (1 - lam) * np.mean(X[I3]**2) + lam * np.mean(X[I1]**2) - np.mean(X[I2]**2)

        if den == 0:
            return np.array([np.nan] * 11)

        # Delta is lower bound on M
        Delta = 2 * (lam * mean_Y1 + (1 - lam) * mean_Y3 - mean_Y2) / den

        # Variance of Delta
        VD = 4 * (
            lam**2 * np.mean(s2[I1]) / np.sum(I1) +
            (1 - lam)**2 * np.mean(s2[I3]) / np.sum(I3) +
            np.mean(s2[I2]) / np.sum(I2)
        ) / den**2

        return np.array([
            Delta, np.sqrt(VD), mean_Y1, mean_Y2, mean_Y3,
            np.min(X[I1]), np.max(X[I1]),
            np.min(X[I2]), np.max(X[I2]),
            np.min(X[I3]), np.max(X[I3])
        ])

    # Unique values on each side
    xp = np.sort(np.unique(X[d.p]))
    xm = np.sort(np.unique(np.abs(X[d.m])))

    def Dpj(j):
        return dk(Y[d.p], X[d.p], xp, d.sigma2[d.p], j)

    def Dmj(j):
        return dk(Y[d.m], np.abs(X[d.m]), xm, d.sigma2[d.m], j)

    Sp = len(xp) // (3 * s)
    Sm = len(xm) // (3 * s)

    if min(Sp, Sm) == 0:
        raise ValueError("Value of s is too big")

    if not multiple:
        Sp = Sm = 1

    # Compute curvature estimates
    Dp = np.column_stack([Dpj(j+1) for j in range(Sp)])
    Dm = np.column_stack([Dmj(j+1) for j in range(Sm)])

    def critical_value(M, Z, sd, alpha):
        """Critical value for testing."""
        if Z.shape[1] == 1:
            return cvb(M / sd, alpha=alpha)
        else:
            # Simulate
            S = Z + M * (1 / sd)[np.newaxis, :]
            maxS = np.abs(S[np.arange(Z.shape[0]), np.argmax(S, axis=1)])
            return np.quantile(maxS, 1 - alpha)

    def hat_m(D):
        """Compute point estimate and CI for M."""
        ts = np.abs(D[0, :] / D[1, :])  # sup_t statistic
        max_idx = np.argmax(ts)
        maxt = D[:, max_idx]

        # Simulate
        np.random.seed(42)
        Z = np.random.randn(10000, D.shape[1])

        # Median unbiased estimate
        hatm = 0.0
        if np.max(ts) > critical_value(0, Z, D[1, :], 0.5):
            try:
                hatm = find_zero(
                    lambda m: np.max(ts) - critical_value(m, Z, D[1, :], 0.5),
                    negative=False
                )
            except:
                hatm = 0.0

        # Lower confidence bound
        lower = 0.0
        if np.max(ts) >= critical_value(0, Z, D[1, :], alpha):
            try:
                lower = find_zero(
                    lambda m: np.max(ts) - critical_value(m, Z, D[1, :], alpha),
                    negative=False
                )
            except:
                lower = 0.0

        return {
            'estimate': hatm,
            'conf.low': lower,
            'diagnostics': {
                'Delta': maxt[0], 'sdDelta': maxt[1],
                'y1': maxt[2], 'y2': maxt[3], 'y3': maxt[4],
            }
        }

    if separate:
        po = hat_m(Dp)
        ne = hat_m(Dm)
        ret = pd.DataFrame({
            'estimate': [ne['estimate'], po['estimate']],
            'conf.low': [ne['conf.low'], po['conf.low']]
        }, index=['Below cutoff', 'Above cutoff'])
    else:
        D_combined = np.column_stack([Dm, Dp])
        result = hat_m(D_combined)
        ret = pd.DataFrame({
            'estimate': [result['estimate']],
            'conf.low': [result['conf.low']]
        }, index=['Pooled'])

    return ret
