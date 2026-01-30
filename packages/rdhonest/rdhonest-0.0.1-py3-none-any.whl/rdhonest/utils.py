"""
Utility functions and data classes for RDHonest.
"""

import numpy as np
from scipy import optimize
from dataclasses import dataclass, field
from typing import Optional, Union, List
import pandas as pd


@dataclass
class RDData:
    """Base class for RD data structures."""
    X: np.ndarray  # Running variable (centered at cutoff)
    Y: np.ndarray  # Outcome variable(s)
    orig_cutoff: float  # Original cutoff value
    p: np.ndarray  # Boolean: observations at or above cutoff
    m: np.ndarray  # Boolean: observations below cutoff
    weights: np.ndarray  # Observation weights
    clusterid: Optional[np.ndarray] = None
    covs: Optional[np.ndarray] = None  # Covariates
    sigma2: Optional[np.ndarray] = None  # Variance estimates
    est_w: Optional[np.ndarray] = None  # Estimation weights
    rho: Optional[float] = None  # Moulton clustering adjustment
    Y_unadj: Optional[np.ndarray] = None  # Unadjusted outcome


@dataclass
class SRDData(RDData):
    """Sharp RD data class."""
    pass


@dataclass
class FRDData(RDData):
    """Fuzzy RD data class."""
    pass


@dataclass
class IPData(RDData):
    """Inference at a point data class."""
    pass


@dataclass
class RDResults:
    """Results from RD estimation."""
    coefficients: pd.DataFrame
    data: RDData
    lm: Optional[object] = None  # Linear model fit
    call: Optional[dict] = None
    na_action: Optional[object] = None
    delta: Optional[float] = None  # For optimal kernel
    omega: Optional[float] = None  # For optimal kernel

    def __repr__(self):
        return self._format_output()

    def _format_output(self):
        """Format output similar to R's print.RDResults."""
        co = self.coefficients.iloc[0]

        lines = []
        if self.call:
            lines.append(f"\nCall: RDHonest(...)")

        lines.append(f"\nInference for {co['term']} (using {co['method']} class), "
                    f"confidence level {100 * (1 - co['alpha']):.0f}%:")

        # Format main results
        lines.append(f"\n{'Estimate':<15} {'Std. Error':<15} {'Maximum Bias':<15} "
                    f"{'Confidence Interval':<25}")
        lines.append(f"{co['estimate']:<15.6f} {co['std.error']:<15.6f} "
                    f"{co['maximum.bias']:<15.6f} "
                    f"({co['conf.low']:.6f}, {co['conf.high']:.6f})")

        lines.append(f"\nOnesided CIs: (-Inf, {co['conf.high.onesided']:.6f}), "
                    f"({co['conf.low.onesided']:.6f}, Inf)")

        if 'eff.obs' in co:
            lines.append(f"\nNumber of effective observations: {co['eff.obs']:.2f}")
        if 'leverage' in co:
            lines.append(f"Maximal leverage: {co['leverage']:.6f}")

        if 'first.stage' in co and pd.notna(co.get('first.stage')):
            lines.append(f"First stage estimate: {co['first.stage']:.6f}")
            lines.append(f"First stage smoothness constant M: {co['M.fs']:.6f}")
            lines.append(f"Reduced form smoothness constant M: {co['M.rf']:.6f}")
        elif 'M' in co and pd.notna(co.get('M')):
            lines.append(f"Smoothness constant M: {co['M']:.6f}")

        if 'p.value' in co:
            lines.append(f"P-value: {co['p.value']:.6f}")

        if 'bandwidth' in co and pd.notna(co.get('bandwidth')):
            lines.append(f"\nBased on local regression with bandwidth: {co['bandwidth']:.6f}, "
                        f"kernel: {co.get('kernel', 'unknown')}")
        elif 'bandwidth.m' in co:
            lines.append(f"\nSmoothing parameters below and above cutoff: "
                        f"{co['bandwidth.m']:.6f}, {co['bandwidth.p']:.6f}")

        return "\n".join(lines)


def create_rd_data(
    Y: np.ndarray,
    X: np.ndarray,
    cutoff: float = 0.0,
    method: str = "SRD",
    weights: Optional[np.ndarray] = None,
    covs: Optional[np.ndarray] = None,
    clusterid: Optional[np.ndarray] = None,
    sigma2: Optional[np.ndarray] = None,
) -> RDData:
    """
    Create an RD data object from arrays.

    Parameters
    ----------
    Y : np.ndarray
        Outcome variable(s). For FRD, should be 2D with columns [outcome, treatment].
    X : np.ndarray
        Running variable.
    cutoff : float
        RD cutoff value.
    method : str
        One of 'SRD', 'FRD', or 'IP'.
    weights : np.ndarray, optional
        Observation weights.
    covs : np.ndarray, optional
        Covariate matrix.
    clusterid : np.ndarray, optional
        Cluster identifiers.
    sigma2 : np.ndarray, optional
        Supplied variance estimates.

    Returns
    -------
    RDData
        Data object for RD analysis.
    """
    X = np.asarray(X).flatten()
    Y = np.asarray(Y)
    if Y.ndim == 1:
        Y = Y.reshape(-1, 1)

    # Center X at cutoff
    X_centered = X - cutoff

    # Sort by X
    sort_idx = np.argsort(X_centered)
    X_centered = X_centered[sort_idx]
    Y = Y[sort_idx]

    if weights is None:
        weights = np.ones(len(X_centered))
    else:
        weights = np.asarray(weights)[sort_idx]

    if covs is not None:
        covs = np.asarray(covs)[sort_idx]

    if clusterid is not None:
        clusterid = np.asarray(clusterid)[sort_idx]

    if sigma2 is not None:
        sigma2 = np.asarray(sigma2)[sort_idx]

    p = X_centered >= 0
    m = X_centered < 0

    data_class = {"SRD": SRDData, "FRD": FRDData, "IP": IPData}[method]

    return data_class(
        X=X_centered,
        Y=Y,
        orig_cutoff=cutoff,
        p=p,
        m=m,
        weights=weights,
        clusterid=clusterid,
        covs=covs,
        sigma2=sigma2,
    )


def find_zero(f, ival: float = 1.1, negative: bool = True) -> float:
    """
    Find interval containing zero of a function, then find the zero.

    Parameters
    ----------
    f : callable
        Function whose root we're looking for.
    ival : float
        Upper endpoint of initial interval.
    negative : bool
        If True, lower endpoint is -ival; otherwise 1/ival.

    Returns
    -------
    float
        Root of the function.
    """
    def minval(ival):
        return -ival if negative else min(1/ival, 1e-3)

    # Expand interval until sign changes
    max_iter = 100
    for _ in range(max_iter):
        try:
            f_upper = f(ival)
            f_lower = f(minval(ival))
            if np.sign(f_upper) != np.sign(f_lower):
                break
        except:
            pass
        ival = 2 * ival

    result = optimize.brentq(f, minval(ival), ival, xtol=np.finfo(float).eps**0.75)
    return result


def golden_section_search(f, xs: np.ndarray) -> float:
    """
    Modified golden section search for unimodal piecewise constant function.

    Parameters
    ----------
    f : callable
        Objective function.
    xs : np.ndarray
        Support points (sorted).

    Returns
    -------
    float
        Optimal value from the support.
    """
    gr = (np.sqrt(5) + 1) / 2
    a = 0
    b = len(xs) - 1
    c = int(round(b - (b - a) / gr))
    d = int(round(a + (b - a) / gr))

    while b - a > 100:
        if f(xs[c]) < f(xs[d]):
            b = d
        else:
            a = c
        c = int(round(b - (b - a) / gr))
        d = int(round(a + (b - a) / gr))

    supp = xs[a:b+1]
    values = np.array([f(x) for x in supp])
    return supp[np.argmin(values)]


def check_positive(x, length: int) -> bool:
    """Check if x is a non-negative numeric vector of given length."""
    x = np.atleast_1d(x)
    return len(x) == length and np.all(x >= 0)


def kernel_type(kern) -> str:
    """
    Get kernel type string.

    Parameters
    ----------
    kern : str or callable
        Kernel specification.

    Returns
    -------
    str
        Kernel type.
    """
    valid_kernels = ["optimal", "uniform", "triangular", "epanechnikov"]
    if callable(kern):
        return "function"
    elif isinstance(kern, str) and kern in valid_kernels:
        return kern
    else:
        raise ValueError(f"'kern' must be a function or one of: {valid_kernels}")


def process_options(M, se_method: str, method: str, d: RDData, kern):
    """Validate options for RD estimation."""
    ktype = kernel_type(kern)

    if ktype == "optimal" and method != "SRD":
        raise ValueError("Optimal kernel requires sharp RD design.")

    m_len = 2 if method == "FRD" else 1
    if M is not None:
        if not check_positive(M, m_len):
            raise ValueError(f"M must be a non-negative numeric vector of length {m_len}.")

    if method == "IP":
        if d.covs is not None:
            raise ValueError("Covariates not allowed when method is 'IP'.")
    else:
        if min(np.sum(d.p), np.sum(d.m)) == 0:
            raise ValueError("No observations on one side of the cutoff")

    valid_se_methods = ["nn", "EHW", "supplied.var"]
    if se_method not in valid_se_methods:
        raise ValueError(f"se_method must be one of: {valid_se_methods}")

    if se_method == "nn" and d.clusterid is not None:
        raise ValueError("'se_method=\"nn\"' not allowed with clustered standard errors. "
                        "Use 'se_method=\"EHW\"'")
