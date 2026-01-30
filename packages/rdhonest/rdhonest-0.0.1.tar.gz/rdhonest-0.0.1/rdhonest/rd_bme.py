"""
RDHonestBME: Honest CIs in sharp RD with discrete regressors under BME function class.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Union

from .utils import RDResults, create_rd_data


def rd_lp_formula(order: int) -> str:
    """Generate local polynomial formula string."""
    if order > 0:
        terms = [f"x**{p}" for p in range(1, order + 1)]
        f1 = f"({' + '.join(terms)}) * (x >= 0)"
    else:
        f1 = "(x >= 0)"
    return f"y ~ {f1}"


def rd_honest_bme(
    Y: np.ndarray,
    X: np.ndarray,
    cutoff: float = 0.0,
    h: float = np.inf,
    alpha: float = 0.05,
    order: int = 0,
    subset: Optional[np.ndarray] = None,
) -> RDResults:
    """
    Honest CIs in sharp RD with discrete regressors under BME function class.

    Computes honest CIs for local polynomial regression with uniform kernel in
    sharp RD under the bounded misspecification error (BME) class.

    Parameters
    ----------
    Y : np.ndarray
        Outcome variable.
    X : np.ndarray
        Running variable.
    cutoff : float
        RD cutoff.
    h : float
        Bandwidth (default: Inf for all data).
    alpha : float
        Significance level.
    order : int
        Order of local polynomial (0=constant, 1=linear, etc.).
    subset : np.ndarray, optional
        Boolean array for subsetting.

    Returns
    -------
    RDResults
        Estimation results.

    Examples
    --------
    >>> results = rd_honest_bme(log_earnings, yearat14, cutoff=1947, h=3, order=1)
    """
    Y = np.asarray(Y).flatten()
    X = np.asarray(X).flatten()

    # Center X at cutoff
    x = X - cutoff

    # Apply subset
    if subset is not None:
        x = x[subset]
        Y = Y[subset]

    # Drop observations outside bandwidth
    ind = (x <= h) & (x >= -h)
    x = x[ind]
    y = Y[ind]
    n = len(y)

    # Count effective support points
    support = np.sort(np.unique(x))
    G = len(support)
    Gm = np.sum(support < 0)

    # Create design matrix for actual model
    # y ~ I(x>=0) + x + I(x>=0)*x + ... (depending on order)
    indicator = (x >= 0).astype(float)

    # Build design matrix
    cols = [np.ones(n)]  # Intercept
    if order > 0:
        for p in range(1, order + 1):
            cols.append(x**p)
    cols.append(indicator)
    if order > 0:
        for p in range(1, order + 1):
            cols.append(indicator * x**p)

    X1 = np.column_stack(cols)

    # Dummied out model: saturated with support point dummies
    X2 = np.zeros((n, G))
    for i, s in enumerate(support):
        X2[:, i] = (x == s).astype(float)

    # Fit models using OLS
    # Model 1: local polynomial
    coeffs1 = np.linalg.lstsq(X1, y, rcond=None)[0]
    fitted1 = X1 @ coeffs1
    resid1 = y - fitted1

    # Model 2: saturated
    coeffs2 = np.linalg.lstsq(X2, y, rcond=None)[0]
    resid2 = y - X2 @ coeffs2

    # Delta: difference between saturated and polynomial predictions at support points
    # delta = coeffs2 - X1_support @ coeffs1
    X1_support = np.zeros((G, X1.shape[1]))
    for i, s in enumerate(support):
        row = [1.0]
        if order > 0:
            for p in range(1, order + 1):
                row.append(s**p)
        row.append(float(s >= 0))
        if order > 0:
            for p in range(1, order + 1):
                row.append(float(s >= 0) * s**p)
        X1_support[i, :] = row

    delta = coeffs2 - X1_support @ coeffs1

    # Compute joint VCOV matrix
    # Q^{-1} for each model
    try:
        Q1inv = np.linalg.inv(X1.T @ X1)
        Q2inv = np.linalg.inv(X2.T @ X2)
    except np.linalg.LinAlgError:
        Q1inv = np.linalg.pinv(X1.T @ X1)
        Q2inv = np.linalg.pinv(X2.T @ X2)

    # Sandwich variance
    meat1 = (X1 * resid1[:, np.newaxis]).T @ (X1 * resid1[:, np.newaxis])
    meat2 = (X2 * resid2[:, np.newaxis]).T @ (X2 * resid2[:, np.newaxis])

    V1 = Q1inv @ meat1 @ Q1inv
    V2 = Q2inv @ meat2 @ Q2inv

    # Cross covariance
    meat12 = (X1 * resid1[:, np.newaxis]).T @ (X2 * resid2[:, np.newaxis])
    V12 = Q1inv @ meat12 @ Q2inv

    # Build combined variance matrix
    k1 = X1.shape[1]
    k2 = X2.shape[1]
    v_m1m2 = np.block([
        [V1, V12],
        [V12.T, V2]
    ])

    # Index for RD parameter (treatment indicator coefficient)
    # In our construction, it's at position order+1 (0-indexed: order+1)
    param_idx = order + 1

    # Build transformation matrix
    # e2 selects the treatment coefficient from model 1
    e2 = np.zeros(k1 + k2)
    e2[param_idx] = 1

    # aa matrix transforms to (delta, tau)
    # delta_i = coef2_i - X1_support[i,:] @ coef1
    aa = np.zeros((G + 1, k1 + k2))
    aa[:G, :k1] = -X1_support
    aa[:G, k1:k1+k2] = np.eye(G)
    aa[G, :] = e2

    vdt = aa @ v_m1m2 @ aa.T

    # All possible combinations of g_-, g_+, s_-, s_+
    # g_- in {0, ..., Gm-1}, g_+ in {Gm, ..., G-1}
    # s_-, s_+ in {-1, +1}
    from itertools import product

    combinations = []
    for gm in range(Gm):
        for gp in range(Gm, G):
            for sm in [-1, 1]:
                for sp in [-1, 1]:
                    combinations.append((gm, gp, sm, sp))

    combinations = np.array(combinations)
    n_comb = len(combinations)

    # Build selection vectors
    selvec = np.zeros((n_comb, G + 1))
    for i, (gm, gp, sm, sp) in enumerate(combinations):
        selvec[i, gm] = sm
        selvec[i, gp] = sp
        selvec[i, G] = 1  # Add tau

    # Compute SE and deviations
    se = np.sqrt(np.sum((selvec @ vdt) * selvec, axis=1))
    dev = selvec[:, :G] @ delta

    # Upper and lower CIs
    tau = coeffs1[param_idx]
    ci_l = tau + dev - stats.norm.ppf(1 - alpha/2) * se
    ci_u = tau + dev + stats.norm.ppf(1 - alpha/2) * se

    # One-sided
    oci_l = tau + dev - stats.norm.ppf(1 - alpha) * se
    oci_u = tau + dev + stats.norm.ppf(1 - alpha) * se

    # Compute estimation weights for leverage
    try:
        Q1_qr = np.linalg.qr(X1)
        R1_inv = np.linalg.inv(Q1_qr[1])
        wt = R1_inv[param_idx, :] @ Q1_qr[0].T
        leverage = np.max(wt**2) / np.sum(wt**2) if np.sum(wt**2) > 0 else 0
    except:
        leverage = np.nan

    # Find worst-case bounds
    l_idx = np.argmin(ci_l)
    u_idx = np.argmax(ci_u)

    # Build results
    co = {
        'term': 'Sharp RD parameter',
        'estimate': tau,
        'std.error': np.sqrt(vdt[G, G]),
        'maximum.bias': max(np.abs(dev[u_idx]), np.abs(dev[l_idx])),
        'conf.low': ci_l[l_idx],
        'conf.high': ci_u[u_idx],
        'conf.low.onesided': np.min(oci_l),
        'conf.high.onesided': np.max(oci_u),
        'bandwidth': h,
        'eff.obs': n,
        'leverage': leverage,
        'cv': np.nan,
        'alpha': alpha,
        'method': 'BME',
        'kernel': 'uniform',
        'M': np.nan,
        'M.rf': np.nan,
        'M.fs': np.nan,
        'first.stage': np.nan,
    }

    # P-value
    co['p.value'] = (
        stats.norm.cdf(co['maximum.bias'] - np.abs(co['estimate'] / co['std.error'])) +
        stats.norm.cdf(-co['maximum.bias'] - np.abs(co['estimate'] / co['std.error']))
    )

    co_df = pd.DataFrame([co])

    # Create dummy data object
    d = create_rd_data(Y=y, X=x+cutoff, cutoff=cutoff, method="SRD")

    return RDResults(coefficients=co_df, data=d, lm={'coefficients': coeffs1})


def RDHonestBME(
    formula: Optional[str] = None,
    data: Optional[pd.DataFrame] = None,
    Y: Optional[np.ndarray] = None,
    X: Optional[np.ndarray] = None,
    cutoff: float = 0.0,
    h: float = np.inf,
    alpha: float = 0.05,
    order: int = 0,
    subset: Optional[np.ndarray] = None,
) -> RDResults:
    """
    R-style interface for rd_honest_bme.

    Can be called with either:
    1. formula + data: "outcome ~ running_var"
    2. Y, X arrays

    Parameters
    ----------
    formula : str, optional
        R-style formula "Y ~ X".
    data : pd.DataFrame, optional
        DataFrame with variables.
    Y : np.ndarray, optional
        Outcome array.
    X : np.ndarray, optional
        Running variable array.
    cutoff : float
        RD cutoff.
    h : float
        Bandwidth.
    alpha : float
        Significance level.
    order : int
        Polynomial order.
    subset : np.ndarray, optional
        Boolean subset array.

    Returns
    -------
    RDResults
        Estimation results.
    """
    if formula is not None and data is not None:
        parts = formula.split("~")
        Y_name = parts[0].strip()
        X_name = parts[1].strip()
        Y = data[Y_name].values
        X = data[X_name].values
        if subset is not None:
            Y = Y[subset]
            X = X[subset]
            subset = None  # Already applied
    elif Y is None or X is None:
        raise ValueError("Must provide either (formula, data) or (Y, X)")

    return rd_honest_bme(Y=Y, X=X, cutoff=cutoff, h=h, alpha=alpha, order=order, subset=subset)
