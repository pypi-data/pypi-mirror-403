"""
Optimal estimators under Taylor smoothness class for RD.
"""

import numpy as np
from scipy import optimize, stats
from typing import Optional, Tuple, Callable
import warnings
import pandas as pd

from .utils import RDData, RDResults, find_zero
from .cvb import cvb, fill_coefs
from .variance import prelim_var, sigma_nn
from .npr import np_reg


def q_func(d: RDData, f: Callable) -> float:
    """
    Compute inverse modulus squared divided by 4.

    Q = sum_i g(x_i)^2 / sigma^2(x_i)

    Parameters
    ----------
    d : RDData
        RD data object.
    f : callable
        Least favorable function.

    Returns
    -------
    float
        Q value.
    """
    fx = f(d.X.flatten())
    return np.sum(fx**2 / d.sigma2)


def sacks_ylvisaker(x, b, d_param, C):
    """
    Sacks-Ylvisaker function: g(x) = (b + dx - Cx^2)_+ - (b + dx + Cx^2)_-

    Parameters
    ----------
    x : array-like
        X values.
    b : float
        Jump at zero.
    d_param : float
        Slope parameter.
    C : float
        Smoothness parameter.

    Returns
    -------
    np.ndarray
        Function values.
    """
    x = np.asarray(x)
    term = b + d_param * x - C * x**2
    term_neg = b + d_param * x + C * x**2
    return np.maximum(term, 0) + np.minimum(term_neg, 0)


def rd_gbc(d: RDData, b: float, C: float) -> Callable:
    """
    Solution to inverse modulus problem in RD under Taylor(2) class.

    Compute function g_{b,C}(x) that solves the inverse modulus problem.

    Parameters
    ----------
    d : RDData
        RD data object.
    b : float
        Jump at zero.
    C : float
        Smoothness parameter (M/2).

    Returns
    -------
    callable
        The least favorable function.
    """
    X = d.X.flatten()
    sigma2 = d.sigma2

    def dstar(X_sub, b_sub, C_sub, sigma2_sub):
        """Find d for Sacks-Ylvisaker function."""
        def eq(d_param):
            sy = sacks_ylvisaker(X_sub, b_sub, d_param, C_sub)
            return np.sum(sy * X_sub / sigma2_sub)
        return find_zero(eq)

    def eq_bm(bm):
        """Find b_minus."""
        X_m = X[d.m]
        X_p = X[d.p]
        sigma2_m = sigma2[d.m]
        sigma2_p = sigma2[d.p]

        dm = dstar(X_m, bm, C, sigma2_m)
        dp = dstar(X_p, b - bm, C, sigma2_p)

        sy_p = sacks_ylvisaker(X_p, b - bm, dp, C)
        sy_m = sacks_ylvisaker(X_m, bm, dm, C)

        return np.sum(sy_p / sigma2_p) - np.sum(sy_m / sigma2_m)

    bm = find_zero(eq_bm, b)
    bp = b - bm
    dp = dstar(X[d.p], bp, C, sigma2[d.p])
    dm = dstar(X[d.m], bm, C, sigma2[d.m])

    def lf_function(x):
        x = np.asarray(x)
        result = np.zeros_like(x, dtype=float)
        result[x >= 0] = sacks_ylvisaker(x[x >= 0], bp, dp, C)
        result[x < 0] = -sacks_ylvisaker(x[x < 0], bm, dm, C)
        return result

    return lf_function


def rd_lf_function(d: RDData, C: float, delta: float) -> Callable:
    """
    Solve modulus problem in RD under Taylor(2) class.

    Parameters
    ----------
    d : RDData
        RD data object.
    C : float
        Smoothness parameter (M/2).
    delta : float
        Delta parameter.

    Returns
    -------
    callable
        Least favorable function.
    """
    def eq(b):
        f = rd_gbc(d, b, C)
        return 4 * q_func(d, f) - delta**2

    b_opt = find_zero(eq, negative=False)
    return rd_gbc(d, b_opt, C)


def rd_t_estimator(
    d: RDData,
    f: Callable,
    alpha: float,
    se_method: str,
    J: int = 3
) -> RDResults:
    """
    Compute optimal estimator based on solution to modulus problem.

    Parameters
    ----------
    d : RDData
        RD data object.
    f : callable
        Least favorable function.
    alpha : float
        Significance level.
    se_method : str
        SE method.
    J : int
        Number of nearest neighbors.

    Returns
    -------
    RDResults
        Estimation results.
    """
    X = d.X.flatten()
    Y = d.Y.flatten() if d.Y.ndim == 1 else d.Y[:, 0]

    # Denominator
    fx_p = f(X[d.p])
    den = np.sum(fx_p / d.sigma2[d.p])

    # Weights
    fx = f(X)
    W = fx / (d.sigma2 * den)

    q = q_func(d, f)

    # Variance estimation
    if se_method == "nn":
        sigma2_p = sigma_nn(X[d.p], Y[d.p], J=J)
        sigma2_m = sigma_nn(X[d.m], Y[d.m], J=J)
        sigma2 = np.zeros(len(X))
        sigma2[d.p] = sigma2_p
        sigma2[d.m] = sigma2_m
    else:
        sigma2 = d.sigma2

    # Estimate
    Lhat = np.sum(W * Y)
    b = f(0) - f(-1e-10)  # Jump at zero
    sd = np.sqrt(np.sum(W**2 * sigma2))
    maxbias = b - q / den

    # Effective observations
    r_u = np_reg(d, np.max(np.abs(X[W != 0])), kern="uniform")
    w_u = r_u['est_w']
    eff_obs = r_u['eff_obs'] * np.sum(w_u**2) / np.sum(W**2) if np.sum(W**2) > 0 else 0

    d.est_w = W

    co = {
        'term': 'Sharp RD parameter',
        'estimate': Lhat,
        'std.error': sd,
        'maximum.bias': maxbias,
        'conf.low': np.nan,
        'conf.high': np.nan,
        'conf.low.onesided': np.nan,
        'conf.high.onesided': np.nan,
        'bandwidth.m': np.nan,
        'bandwidth.p': np.nan,
        'eff.obs': eff_obs,
        'leverage': np.max(W**2) / np.sum(W**2) if np.sum(W**2) > 0 else 0,
        'cv': np.nan,
        'alpha': alpha,
        'method': 'Taylor',
        'M': np.nan,
        'M.rf': np.nan,
        'M.fs': np.nan,
        'first.stage': np.nan,
        'kernel': 'optimal',
        'p.value': np.nan,
    }

    co = fill_coefs(co)
    co_df = pd.DataFrame([co])

    return RDResults(
        coefficients=co_df,
        data=d,
        lm=None,
        delta=np.sqrt(4 * q),
        omega=2 * b,
    )


def rd_t_opt(
    d: RDData,
    M: float,
    opt_criterion: str,
    alpha: float,
    beta: float,
    se_method: str,
    J: int = 3
) -> RDResults:
    """
    Optimal inference in RD under Taylor class.

    Parameters
    ----------
    d : RDData
        RD data object.
    M : float
        Smoothness constant.
    opt_criterion : str
        "MSE", "FLCI", or "OCI".
    alpha : float
        Significance level.
    beta : float
        For OCI criterion.
    se_method : str
        SE method.
    J : int
        Number of nearest neighbors.

    Returns
    -------
    RDResults
        Estimation results.
    """
    # Check for supplied variance
    if d.sigma2 is None:
        d = prelim_var(d, se_initial="EHW")

    if d.clusterid is not None:
        warnings.warn("Optimal kernel can only be used with independent data. "
                     "Ignoring clusterid")

    C = M / 2

    # Find optimal delta
    if opt_criterion == "OCI":
        delta = stats.norm.ppf(1 - alpha) + stats.norm.ppf(beta)
        lff = rd_lf_function(d, C, delta)

    elif opt_criterion == "MSE":
        def eq(b):
            f = rd_gbc(d, b, C)
            fx = f(d.X.flatten())
            return C * np.sum(d.X.flatten()**2 * np.abs(fx) / d.sigma2) - 1
        b_opt = find_zero(eq, negative=False)
        lff = rd_gbc(d, b_opt, C)

    elif opt_criterion == "FLCI":
        def eq(b):
            f = rd_gbc(d, b, C)
            q = q_func(d, f)
            fx_p = f(d.X.flatten()[d.p])
            den = np.sum(fx_p / d.sigma2[d.p])
            hse = np.sqrt(q) / den
            maxbias = b - q / den
            return cvb(maxbias / hse, alpha) * hse

        # Start around MSE optimal b
        r_mse = rd_t_opt(d, M, "MSE", alpha, beta, se_method, J)
        bs = r_mse.omega / 2

        # Optimize
        result = optimize.minimize_scalar(eq, bounds=(bs/2, 3*bs/2), method='bounded')
        lff = rd_gbc(d, result.x, C)

    # Compute optimal estimator
    r = rd_t_estimator(d, lff, alpha, se_method, J)

    # Compute bandwidths
    bw_m = np.sqrt(-lff(-1e-10) / C) if lff(-1e-10) < 0 else 0
    bw_p = np.sqrt(lff(0) / C) if lff(0) > 0 else 0

    r.coefficients.loc[0, 'bandwidth.m'] = bw_m
    r.coefficients.loc[0, 'bandwidth.p'] = bw_p
    r.coefficients.loc[0, 'M'] = M

    return r


def rd_t_efficiency_bound(
    obj: RDResults,
    opt_criterion: str = "FLCI",
    beta: float = 0.5
) -> float:
    """
    Finite-sample efficiency bounds for minimax CIs.

    Parameters
    ----------
    obj : RDResults
        Result of rd_honest call.
    opt_criterion : str
        "FLCI" or "OCI".
    beta : float
        For OCI criterion.

    Returns
    -------
    float
        Efficiency bound.
    """
    d = obj.data
    alpha = obj.coefficients.iloc[0]['alpha']
    C = obj.coefficients.iloc[0]['M'] / 2
    d = prelim_var(d, se_initial="EHW")

    if opt_criterion == "OCI":
        delta = stats.norm.ppf(1 - alpha) + stats.norm.ppf(beta)
        r1 = rd_t_estimator(d, rd_lf_function(d, C, delta), alpha, "supplied.var")
        r2 = rd_t_estimator(d, rd_lf_function(d, C, 2*delta), alpha, "supplied.var")
        return r2.omega / (r1.delta * r1.coefficients.iloc[0]['std.error'] + r1.omega)

    else:  # FLCI
        def deltat(t):
            return np.sqrt(q_func(d, rd_gbc(d, t, C)))

        def integrand(t):
            return stats.norm.cdf(stats.norm.ppf(1 - alpha) - deltat(t))

        # Upper cutoff
        upper = 10
        while integrand(upper) > 1e-10:
            upper *= 2

        from scipy import integrate
        num, _ = integrate.quad(integrand, 1e-6, upper)

        r_flci = rd_t_opt(d, 2*C, "FLCI", alpha, beta, "supplied.var")
        den = (r_flci.coefficients.iloc[0]['conf.high'] -
               r_flci.coefficients.iloc[0]['conf.low']) / 2

        return num / den
