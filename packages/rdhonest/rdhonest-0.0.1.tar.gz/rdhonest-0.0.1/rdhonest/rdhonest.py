"""
Main RDHonest function for honest inference in RD designs.
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
from typing import Optional, Union, Tuple
import warnings

from .utils import (
    RDData, SRDData, FRDData, IPData, RDResults,
    create_rd_data, kernel_type, process_options, golden_section_search
)
from .kernels import eq_kern
from .cvb import cvb, fill_coefs
from .variance import prelim_var
from .npr import np_reg, mrot
from .rd_opt import rd_t_opt


def rd_honest(
    Y: np.ndarray,
    X: np.ndarray,
    cutoff: float = 0.0,
    M: Optional[Union[float, np.ndarray]] = None,
    kern: str = "triangular",
    h: Optional[float] = None,
    opt_criterion: str = "MSE",
    se_method: str = "nn",
    alpha: float = 0.05,
    beta: float = 0.8,
    J: int = 3,
    sclass: str = "H",
    T0: float = 0.0,
    point_inference: bool = False,
    weights: Optional[np.ndarray] = None,
    covs: Optional[np.ndarray] = None,
    clusterid: Optional[np.ndarray] = None,
    sigma2: Optional[np.ndarray] = None,
    sigmaD2: Optional[np.ndarray] = None,
    sigmaYD: Optional[np.ndarray] = None,
    D: Optional[np.ndarray] = None,
) -> RDResults:
    """
    Honest inference in regression discontinuity designs.

    Calculate estimators and bias-aware CIs for the sharp or fuzzy RD parameter,
    or for the value of the conditional mean at a point.

    Parameters
    ----------
    Y : np.ndarray
        Outcome variable.
    X : np.ndarray
        Running variable.
    cutoff : float
        RD cutoff in the running variable. For inference at a point,
        specifies the point at which to calculate the conditional mean.
    M : float or array-like, optional
        Bound on second derivative of the conditional mean function.
        For fuzzy RD, must be length 2: [M_outcome, M_treatment].
        If not supplied, uses ROT method.
    kern : str
        Kernel function: "triangular", "epanechnikov", "uniform", or "optimal".
    h : float, optional
        Bandwidth. If not supplied, optimal bandwidth is computed.
    opt_criterion : str
        Optimality criterion for bandwidth: "MSE", "FLCI", or "OCI".
    se_method : str
        SE estimation method: "nn", "EHW", or "supplied.var".
    alpha : float
        Determines confidence level 1-alpha.
    beta : float
        Quantile for OCI criterion.
    J : int
        Number of nearest neighbors for NN variance.
    sclass : str
        Smoothness class: "T" for Taylor or "H" for Holder.
    T0 : float
        Initial treatment effect estimate for FRD bandwidth.
    point_inference : bool
        If True, do inference at a point instead of RD.
    weights : np.ndarray, optional
        Observation weights.
    covs : np.ndarray, optional
        Covariates for adjustment.
    clusterid : np.ndarray, optional
        Cluster identifiers.
    sigma2 : np.ndarray, optional
        Supplied variance of outcome.
    sigmaD2 : np.ndarray, optional
        Supplied variance of treatment (FRD only).
    sigmaYD : np.ndarray, optional
        Supplied covariance of treatment and outcome (FRD only).
    D : np.ndarray, optional
        Treatment variable for fuzzy RD.

    Returns
    -------
    RDResults
        Object containing estimates, CIs, and diagnostics.

    Examples
    --------
    >>> # Sharp RD with uniform kernel
    >>> results = rd_honest(voteshare, margin, cutoff=0, kern="uniform", M=0.1, h=10)

    >>> # Fuzzy RD with optimal bandwidth selection
    >>> results = rd_honest(Y, X, D=treatment, cutoff=0, M=[4, 0.4],
    ...                     kern="triangular", opt_criterion="MSE")
    """
    # Determine method
    if point_inference:
        method = "IP"
    elif D is not None:
        method = "FRD"
        Y = np.column_stack([np.asarray(Y).flatten(), np.asarray(D).flatten()])
    else:
        method = "SRD"

    # Create data object
    d = create_rd_data(
        Y=Y, X=X, cutoff=cutoff, method=method,
        weights=weights, covs=covs, clusterid=clusterid, sigma2=sigma2
    )

    # Validate options
    process_options(M, se_method, method, d, kern)

    # Handle covariates: compute bandwidth without, then adjust
    if d.covs is not None and (M is None or h is None):
        d0 = SRDData(
            X=d.X, Y=d.Y, orig_cutoff=d.orig_cutoff,
            p=d.p, m=d.m, weights=d.weights
        )
        M_rot = mrot(d0)
        ret = _npr_honest(d0, M_rot, kern, None, opt_criterion, alpha, beta, se_method, J, sclass, T0)
        h_cov = ret.coefficients.iloc[0]['bandwidth']
        d = _covariate_adjust(d, kern, h_cov)

    # Use ROT for M if not supplied
    if M is None:
        M = mrot(d)
        print(f"Using Armstrong & Kolesar (2020) ROT for smoothness constant M")

    M = np.atleast_1d(M)

    # Optimal kernel or local polynomial
    if kernel_type(kern) == "optimal":
        ret = rd_t_opt(d, M[0], opt_criterion, alpha, beta, se_method, J)
    else:
        ret = _npr_honest(d, M, kern, h, opt_criterion, alpha, beta, se_method, J, sclass, T0)

    # Leverage warning
    leverage = ret.coefficients.iloc[0]['leverage']
    if not np.isfinite(leverage) or leverage > 0.1:
        warnings.warn(f"Maximal leverage is large: {leverage:.2f}. "
                     "Inference may be inaccurate. Consider using bigger bandwidth.")

    # Set term name
    if method == "IP":
        ret.coefficients.loc[0, 'term'] = "Value of conditional mean"
    elif method == "FRD":
        ret.coefficients.loc[0, 'term'] = "Fuzzy RD parameter"
    else:
        ret.coefficients.loc[0, 'term'] = "Sharp RD parameter"

    return ret


def _covariate_adjust(d: RDData, kern: str, h: float) -> RDData:
    """Adjust outcome for covariates."""
    r = np_reg(d, h, kern, order=1, se_method="EHW")
    d.Y_unadj = d.Y.copy()
    d.Y = r['Y_adj']
    return d


def _npr_honest(
    d: RDData,
    M: np.ndarray,
    kern: str = "triangular",
    h: Optional[float] = None,
    opt_criterion: str = "MSE",
    alpha: float = 0.05,
    beta: float = 0.8,
    se_method: str = "nn",
    J: int = 3,
    sclass: str = "H",
    T0: float = 0.0,
    T0bias: bool = False
) -> RDResults:
    """
    NPR honest inference.

    Parameters are similar to rd_honest.
    """
    M = np.atleast_1d(M)

    # Compute optimal bandwidth if not supplied
    if h is None:
        d0 = SRDData(
            X=d.X, Y=d.Y, orig_cutoff=d.orig_cutoff,
            p=d.p, m=d.m, weights=d.weights
        )
        d0.covs = None
        d0.Y_unadj = None
        h = _opt_bw(d0, M, kern, opt_criterion, alpha, beta, sclass, T0)

    # Restore unadjusted Y if available
    if d.Y_unadj is not None:
        d.Y = d.Y_unadj

    # Run local regression
    r1 = np_reg(d, h, kern, order=1, se_method=se_method, J=J)

    wt = r1['est_w']
    ok = wt != 0
    X = d.X.flatten()
    xx = X[ok]
    wt_nz = wt[ok]

    # Check if at boundary
    bd = True
    if isinstance(d, IPData):
        bd = len(np.unique(xx >= 0)) == 1

    # Adjust M for FRD
    if T0bias and isinstance(d, FRDData):
        r1_se = r1['se'] * np.abs(r1['fs'])
        M_adj = np.array([M[0] + M[1] * np.abs(T0), M[0], M[1]])
    elif not T0bias and isinstance(d, FRDData):
        fs = r1['fs']
        M_adj = np.array([
            (M[0] + M[1] * np.abs(r1['estimate'])) / np.abs(fs),
            M[0], M[1]
        ])
    else:
        M_adj = np.array([M[0], np.nan, np.nan])

    # Compute bias
    if r1['eff_obs'] == 0:
        bias = r1_se = np.sqrt(np.finfo(float).max / 10)
    elif sclass == "T":
        bias = M_adj[0] / 2 * np.sum(np.abs(wt_nz * xx**2))
    elif sclass == "H" and bd:
        # At boundary: known form of least favorable function
        bias = M_adj[0] / 2 * np.abs(
            np.sum(wt_nz[xx < 0] * xx[xx < 0]**2) -
            np.sum(wt_nz[xx >= 0] * xx[xx >= 0]**2)
        )
    else:
        # Interior: numerical integration
        def w2p(s):
            mask = xx >= s
            return np.abs(np.sum(wt_nz[mask] * (xx[mask] - s)))

        def w2m(s):
            mask = xx <= s
            return np.abs(np.sum(wt_nz[mask] * (s - xx[mask])))

        from scipy import integrate
        bp, _ = integrate.quad(lambda s: w2p(s), 0, h)
        bm, _ = integrate.quad(lambda s: w2m(s), -h, 0)
        bias = M_adj[0] * (bp + bm)

    method = "Holder" if sclass == "H" else "Taylor"

    # Store estimation weights and variance
    d.est_w = wt
    d.sigma2 = r1['sigma2']

    # Compute leverage
    w_nz = d.weights[ok]
    leverage = np.max(wt_nz**2 / w_nz**2) / np.sum(wt_nz**2 / w_nz) if np.sum(wt_nz**2) > 0 else 0

    # Build coefficients
    co = {
        'term': 'Sharp RD parameter',
        'estimate': r1['estimate'],
        'std.error': r1['se'],
        'maximum.bias': bias,
        'conf.low': np.nan,
        'conf.high': np.nan,
        'conf.low.onesided': np.nan,
        'conf.high.onesided': np.nan,
        'bandwidth': h,
        'eff.obs': r1['eff_obs'],
        'leverage': leverage,
        'cv': np.nan,
        'alpha': alpha,
        'method': method,
        'M': M_adj[0],
        'M.rf': M_adj[1] if len(M_adj) > 1 else np.nan,
        'M.fs': M_adj[2] if len(M_adj) > 2 else np.nan,
        'first.stage': r1['fs'],
        'kernel': kernel_type(kern),
        'p.value': np.nan,
    }

    co = fill_coefs(co)
    co_df = pd.DataFrame([co])

    return RDResults(coefficients=co_df, data=d, lm=r1)


def _opt_bw(
    d: RDData,
    M: np.ndarray,
    kern: str = "triangular",
    opt_criterion: str = "MSE",
    alpha: float = 0.05,
    beta: float = 0.8,
    sclass: str = "H",
    T0: float = 0.0
) -> float:
    """
    Optimal bandwidth selection for nonparametric regression.

    Parameters
    ----------
    d : RDData
        RD data object.
    M : np.ndarray
        Smoothness constants.
    kern : str
        Kernel type.
    opt_criterion : str
        "MSE", "FLCI", or "OCI".
    alpha : float
        Significance level.
    beta : float
        For OCI.
    sclass : str
        Smoothness class.
    T0 : float
        Initial treatment effect.

    Returns
    -------
    float
        Optimal bandwidth.
    """
    # Check if sigma2 is supplied
    if d.sigma2 is None:
        d = prelim_var(d, se_initial="EHW")

    def obj(h_val):
        """Objective function for bandwidth optimization."""
        r = _npr_honest(
            d, M, kern, h_val, alpha=alpha,
            se_method="supplied.var", sclass=sclass, T0=T0, T0bias=True
        )
        co = r.coefficients.iloc[0]

        if opt_criterion == "OCI":
            return (2 * co['maximum.bias'] +
                    co['std.error'] * (stats.norm.ppf(1 - alpha) + stats.norm.ppf(beta)))
        elif opt_criterion == "MSE":
            return co['maximum.bias']**2 + co['std.error']**2
        else:  # FLCI
            return co['conf.high'] - co['conf.low']

    # Minimum bandwidth
    X = d.X.flatten()
    if isinstance(d, IPData):
        unique_abs = np.sort(np.unique(np.abs(X)))
        hmin = unique_abs[1] if len(unique_abs) > 1 else unique_abs[0]
    else:
        unique_p = np.sort(np.unique(X[d.p]))
        unique_m = np.sort(np.unique(np.abs(X[d.m])))
        hmin = max(
            unique_p[1] if len(unique_p) > 1 else unique_p[0],
            unique_m[1] if len(unique_m) > 1 else unique_m[0]
        )

    # Optimize
    if kernel_type(kern) == "uniform":
        supp = np.sort(np.unique(np.abs(X)))
        h = golden_section_search(obj, supp[supp >= hmin])
    else:
        result = optimize.minimize_scalar(
            obj,
            bounds=(hmin, np.max(np.abs(X))),
            method='bounded',
            options={'xatol': np.finfo(float).eps**0.75}
        )
        h = np.abs(result.x)

    return h


# Convenience function matching R interface more closely
def RDHonest(
    formula: Optional[str] = None,
    data: Optional[pd.DataFrame] = None,
    Y: Optional[np.ndarray] = None,
    X: Optional[np.ndarray] = None,
    D: Optional[np.ndarray] = None,
    cutoff: float = 0.0,
    M: Optional[Union[float, np.ndarray]] = None,
    kern: str = "triangular",
    h: Optional[float] = None,
    opt_criterion: str = "MSE",
    se_method: str = "nn",
    alpha: float = 0.05,
    beta: float = 0.8,
    J: int = 3,
    sclass: str = "H",
    T0: float = 0.0,
    point_inference: bool = False,
    weights: Optional[np.ndarray] = None,
    covs: Optional[np.ndarray] = None,
    clusterid: Optional[np.ndarray] = None,
    sigma2: Optional[np.ndarray] = None,
    sigmaD2: Optional[np.ndarray] = None,
    sigmaYD: Optional[np.ndarray] = None,
    subset: Optional[np.ndarray] = None,
) -> RDResults:
    """
    Honest inference in RD - interface similar to R package.

    Can be called with either:
    1. formula + data (R-style): "outcome ~ running_var" or "outcome | treatment ~ running_var"
    2. Y, X arrays (Python-style)

    Parameters
    ----------
    formula : str, optional
        R-style formula.
    data : pd.DataFrame, optional
        DataFrame with variables.
    Y : np.ndarray, optional
        Outcome array.
    X : np.ndarray, optional
        Running variable array.
    D : np.ndarray, optional
        Treatment variable for fuzzy RD.
    ... : other parameters same as rd_honest

    Returns
    -------
    RDResults
        Estimation results.
    """
    # Parse formula if provided
    if formula is not None and data is not None:
        Y, X, D = _parse_formula(formula, data)
        if subset is not None:
            Y = Y[subset]
            X = X[subset]
            if D is not None:
                D = D[subset]
            if weights is not None:
                weights = weights[subset]
            if covs is not None:
                covs = covs[subset]
            if clusterid is not None:
                clusterid = clusterid[subset]

    elif Y is None or X is None:
        raise ValueError("Must provide either (formula, data) or (Y, X)")

    return rd_honest(
        Y=Y, X=X, D=D, cutoff=cutoff, M=M, kern=kern, h=h,
        opt_criterion=opt_criterion, se_method=se_method, alpha=alpha,
        beta=beta, J=J, sclass=sclass, T0=T0, point_inference=point_inference,
        weights=weights, covs=covs, clusterid=clusterid,
        sigma2=sigma2, sigmaD2=sigmaD2, sigmaYD=sigmaYD
    )


def _parse_formula(formula: str, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """
    Parse R-style formula.

    Supports:
    - "Y ~ X" for sharp RD
    - "Y | D ~ X" for fuzzy RD
    """
    # Split by ~
    parts = formula.split("~")
    if len(parts) != 2:
        raise ValueError("Formula must contain exactly one '~'")

    lhs = parts[0].strip()
    rhs = parts[1].strip()

    # Check for fuzzy RD (Y | D)
    if "|" in lhs:
        lhs_parts = lhs.split("|")
        Y_name = lhs_parts[0].strip()
        D_name = lhs_parts[1].strip()
        Y = data[Y_name].values
        D = data[D_name].values
    else:
        Y = data[lhs].values
        D = None

    # Running variable
    X = data[rhs].values

    return Y, X, D
