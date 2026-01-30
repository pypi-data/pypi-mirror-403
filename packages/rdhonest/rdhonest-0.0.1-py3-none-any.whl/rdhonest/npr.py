"""
Nonparametric regression functions for RDHonest.
"""

import numpy as np
import warnings
from typing import Optional, Dict, Any
from .utils import RDData, SRDData, FRDData, IPData
from .kernels import eq_kern
from .variance import sigma_nn


def np_reg(d: RDData, h: float, kern: str = "triangular",
           order: int = 1, se_method: str = "nn", J: int = 3) -> Dict[str, Any]:
    """
    Nonparametric local polynomial regression.

    Calculate fuzzy or sharp RD estimate, or estimate of conditional mean
    at a point, using local polynomial regression.

    Parameters
    ----------
    d : RDData
        RD data object.
    h : float
        Bandwidth.
    kern : str or callable
        Kernel function.
    order : int
        Polynomial order.
    se_method : str
        SE method: "nn", "EHW", or "supplied.var".
    J : int
        Number of nearest neighbors for NN variance.

    Returns
    -------
    dict
        Dictionary with estimate, se, est_w, sigma2, eff_obs, fs, Y_adj, residuals.
    """
    # Get kernel function
    if not callable(kern):
        kern_func = eq_kern(kern, boundary=False, order=0)
    else:
        kern_func = kern

    X = d.X.flatten()
    Y = d.Y if d.Y.ndim > 1 else d.Y.reshape(-1, 1)
    n = len(X)
    ny = Y.shape[1]

    # Kernel weights
    if h <= 0:
        W = np.zeros(n)
    else:
        W = kern_func(X / h) * d.weights

    # Design matrix
    Z = np.column_stack([X**p for p in range(order + 1)])
    Lz = Z.shape[1]

    if not isinstance(d, IPData):
        # Add interaction with treatment indicator for RD
        indicator = (X >= 0).astype(float)
        ZZ = indicator[:, np.newaxis] * Z
        Z = np.column_stack([ZZ, Z])
        if d.covs is not None:
            Z = np.column_stack([Z, d.covs])
        Lz = 2 * (order + 1)

    # Weighted least squares
    W_sqrt = np.sqrt(np.maximum(W, 0))
    Zw = Z * W_sqrt[:, np.newaxis]
    Yw = Y * W_sqrt[:, np.newaxis]

    try:
        Q, R = np.linalg.qr(Zw)
        coeffs = np.linalg.solve(R, Q.T @ Yw)
    except np.linalg.LinAlgError:
        return {
            'estimate': 0.0,
            'se': np.nan,
            'est_w': np.zeros(n),
            'sigma2': np.full(n, np.nan),
            'eff_obs': 0,
            'fs': np.nan,
            'Y_adj': Y,
            'residuals': np.zeros_like(Y),
        }

    # Check for NA coefficients
    if np.any(np.isnan(coeffs[:Lz, :])):
        return {
            'estimate': 0.0,
            'se': np.nan,
            'est_w': np.zeros(n),
            'sigma2': np.full(n, np.nan),
            'eff_obs': 0,
            'fs': np.nan,
            'Y_adj': Y,
            'residuals': np.zeros_like(Y),
        }

    # Handle collinear covariates
    if np.any(np.isnan(coeffs[Lz:, :])):
        # Drop collinear columns
        valid_cols = ~np.any(np.isnan(coeffs), axis=1)
        Z = Z[:, valid_cols[:Z.shape[1]]]
        Zw = Z * W_sqrt[:, np.newaxis]
        Q, R = np.linalg.qr(Zw)
        coeffs = np.linalg.solve(R, Q.T @ Yw)

    # Covariate-adjusted outcome
    Y_adj = Y.copy()
    if Z.shape[1] > Lz:
        Y_adj = Y - Z[:, Lz:] @ coeffs[Lz:, :]

    # Compute estimation weights
    wgt = np.zeros(n)
    ok = W != 0
    if np.any(ok):
        try:
            # Weight for first coefficient (the RD parameter or intercept)
            R_inv = np.linalg.inv(R)
            wgt[ok] = (R_inv[0, :] @ Q[ok, :].T) * W_sqrt[ok]
        except np.linalg.LinAlgError:
            pass

    # Effective observations (rescale against uniform kernel)
    W_u = d.weights * (np.abs(X) <= h)
    Z_u = Z.copy()
    if np.any(W_u > 0):
        try:
            Q_u, R_u = np.linalg.qr(Z_u * np.sqrt(W_u)[:, np.newaxis])
            R_u_inv = np.linalg.inv(R_u)
            wgt_u = (R_u_inv[0, :] @ Q_u.T) * np.sqrt(W_u)

            denom_w = np.sum(wgt**2 / d.weights) if np.sum(wgt**2) > 0 else 1
            denom_u = np.sum(wgt_u**2 / d.weights) if np.sum(wgt_u**2) > 0 else 1
            eff_obs = np.sum(W_u) * denom_u / denom_w if denom_w > 0 else 0
        except np.linalg.LinAlgError:
            eff_obs = np.sum(W_u)
    else:
        eff_obs = 0

    # Residuals
    fitted = Z @ coeffs
    residuals = Y - fitted

    # Squared residuals for HC variance
    def hc_residuals(r):
        """Compute squared residuals matrix for multivariate Y."""
        if r.ndim == 1:
            return r**2
        return np.column_stack([
            r[:, i] * r[:, j]
            for i in range(r.shape[1])
            for j in range(r.shape[1])
        ])

    # Variance for RD: compute separately on either side using adjusted outcome
    def nn_variance(X, Y_adj_local, d):
        """Nearest neighbor variance, computed separately by side for RD."""
        # Flatten Y_adj for variance computation
        Y_flat = Y_adj_local.flatten() if Y_adj_local.ndim > 1 and Y_adj_local.shape[1] == 1 else Y_adj_local

        if isinstance(d, IPData):
            return sigma_nn(X[ok], Y_flat[ok], J, d.weights[ok])
        else:
            res = np.zeros(n)
            if np.any(d.m & ok):
                res[d.m & ok] = sigma_nn(
                    X[d.m & ok], Y_flat[d.m & ok], J, d.weights[d.m & ok]
                )
            if np.any(d.p & ok):
                res[d.p & ok] = sigma_nn(
                    X[d.p & ok], Y_flat[d.p & ok], J, d.weights[d.p & ok]
                )
            return res

    # Compute variance estimate
    if se_method == "nn":
        hsigma2 = nn_variance(X, Y_adj, d)
    elif se_method == "EHW":
        hsigma2 = hc_residuals(residuals)
    elif se_method == "supplied.var":
        hsigma2 = d.sigma2
    else:
        raise ValueError(f"Unknown se_method: {se_method}")

    # Variance computation
    if d.clusterid is None:
        if hsigma2 is not None:
            hsigma2 = np.atleast_1d(hsigma2)
            if hsigma2.ndim == 1:
                V = np.sum(wgt**2 * hsigma2)
            else:
                V = np.sum(wgt[:, np.newaxis]**2 * hsigma2, axis=0)
        else:
            V = np.nan
    elif se_method == "supplied.var":
        rho = d.rho if d.rho is not None else 0
        if hsigma2 is not None:
            V = np.sum(wgt**2 * np.atleast_1d(hsigma2))
            # Add clustering adjustment
            cluster_sums_sq = 0
            for c in np.unique(d.clusterid):
                mask = d.clusterid == c
                cluster_sums_sq += np.sum(wgt[mask])**2
            V += rho * (cluster_sums_sq - np.sum(wgt**2))
        else:
            V = np.nan
    else:  # Cluster-robust SE
        us = residuals * wgt[:, np.newaxis]
        us = us[ok]
        cluster_ids = d.clusterid[ok]
        unique_clusters = np.unique(cluster_ids)
        cluster_sums = np.zeros((len(unique_clusters), ny))
        for i, c in enumerate(unique_clusters):
            mask = cluster_ids == c
            cluster_sums[i, :] = np.sum(us[mask, :], axis=0)
        V = np.sum(cluster_sums**2, axis=0)

    # Extract estimate and SE
    V = np.atleast_1d(V)
    estimate = coeffs[0, 0] if coeffs.shape[1] == 1 else coeffs[0, :]
    se = np.sqrt(V[0]) if len(V) == 1 else np.sqrt(V)

    # Handle FRD
    fs = np.nan
    if isinstance(d, FRDData):
        fs = coeffs[0, 1]  # First stage coefficient
        estimate = coeffs[0, 0] / coeffs[0, 1]
        # Delta method for FRD SE
        if len(V) >= 4:
            grad = np.array([1, -estimate, -estimate, estimate**2])
            se = np.sqrt(np.sum(grad * V[:4])) / np.abs(fs)
        else:
            se = np.nan

    return {
        'estimate': float(estimate) if np.isscalar(estimate) or len(np.atleast_1d(estimate)) == 1 else estimate,
        'se': float(se) if np.isscalar(se) or len(np.atleast_1d(se)) == 1 else se,
        'est_w': wgt,
        'sigma2': hsigma2,
        'eff_obs': eff_obs,
        'fs': fs,
        'Y_adj': Y_adj,
        'residuals': residuals,
        'coefficients': coeffs,
    }


def mrot(d: RDData) -> float:
    """
    Rule of thumb for choosing smoothness constant M.

    Uses global quartic regression to estimate a bound on the second derivative.

    Parameters
    ----------
    d : RDData
        RD data object.

    Returns
    -------
    float or tuple
        For SRD: scalar M.
        For FRD: tuple (M_Y, M_D).
    """
    X = d.X.flatten()
    Y = d.Y.flatten() if d.Y.ndim == 1 else d.Y[:, 0]
    w = d.weights

    if isinstance(d, SRDData):
        # Compute separately on each side
        M_p = _mrot_single(X[d.p], Y[d.p], w[d.p])
        M_m = _mrot_single(X[d.m], Y[d.m], w[d.m])
        return max(M_p, M_m)
    elif isinstance(d, FRDData):
        Y1 = d.Y[:, 0]  # Outcome
        Y2 = d.Y[:, 1]  # Treatment

        M_Y_p = _mrot_single(X[d.p], Y1[d.p], w[d.p])
        M_Y_m = _mrot_single(X[d.m], Y1[d.m], w[d.m])
        M_D_p = _mrot_single(X[d.p], Y2[d.p], w[d.p])
        M_D_m = _mrot_single(X[d.m], Y2[d.m], w[d.m])

        return np.array([max(M_Y_p, M_Y_m), max(M_D_p, M_D_m)])
    else:  # IP
        return _mrot_single(X, Y, w)


def _mrot_single(X: np.ndarray, Y: np.ndarray, w: np.ndarray) -> float:
    """Compute M for a single side/variable."""
    X = X.flatten()
    Y = Y.flatten()

    # Check for sufficient unique values
    if len(np.unique(X)) < 5:
        raise ValueError("Insufficient unique values of running variable to compute ROT for M")

    # Global quartic regression
    Z = np.column_stack([X**p for p in range(5)])
    try:
        # Weighted least squares
        W = np.diag(w)
        coeffs = np.linalg.lstsq(W @ Z, W @ Y, rcond=None)[0]
    except np.linalg.LinAlgError:
        raise ValueError("Could not fit global polynomial for ROT")

    if np.any(np.isnan(coeffs)):
        raise ValueError("Insufficient unique values of running variable to compute ROT for M")

    # Second derivative: 2*r1[2] + 6*x*r1[3] + 12*x^2*r1[4]
    def f2(x):
        return np.abs(2*coeffs[2] + 6*x*coeffs[3] + 12*x**2*coeffs[4])

    # Maximum at endpoints or extremum
    M = max(f2(np.min(X)), f2(np.max(X)))

    if np.abs(coeffs[4]) > 1e-10:
        f2e = -coeffs[3] / (4 * coeffs[4])
        if np.min(X) < f2e < np.max(X):
            M = max(f2(f2e), M)

    return M
