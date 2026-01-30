"""
Variance estimation functions for RDHonest.
"""

import numpy as np
import warnings
from .utils import RDData, SRDData, FRDData, IPData
from .kernels import get_kernel_constants


def sigma_nn(X: np.ndarray, Y: np.ndarray, J: int = 3,
             weights: np.ndarray = None) -> np.ndarray:
    """
    Nearest-neighbor variance estimator.

    Assumes X is sorted.

    Parameters
    ----------
    X : np.ndarray
        Running variable (sorted).
    Y : np.ndarray
        Outcome variable.
    J : int
        Number of nearest neighbors.
    weights : np.ndarray, optional
        Observation weights.

    Returns
    -------
    np.ndarray
        Variance estimates.
    """
    n = len(X)
    Y = np.atleast_2d(Y)
    if Y.shape[0] == n:
        Y = Y  # Already correct shape
    elif Y.shape[1] == n:
        Y = Y.T
    else:
        Y = Y.reshape(-1, 1)

    ny = Y.shape[1] if Y.ndim > 1 else 1
    sigma2 = np.zeros((n, ny**2))

    if weights is None:
        weights = np.ones(n)

    # Use min of J and n-1
    J_actual = min(J, n - 1)

    for k in range(n):
        # Find distances to all other points
        distances = np.abs(X - X[k]).astype(float)
        distances[k] = np.inf  # Exclude self

        # Find J nearest neighbors
        sorted_idx = np.argsort(distances)[:J_actual]
        d_threshold = distances[sorted_idx[-1]]

        # Include all points within this distance (excluding self)
        ind = (np.abs(X - X[k]) <= d_threshold)
        ind[k] = False

        Jk = np.sum(weights[ind])

        if Jk > 0:
            if ny > 1:
                Yk = Y[k, :]
                Yneighbors = Y[ind, :]
                Y_mean = np.sum(weights[ind, np.newaxis] * Yneighbors, axis=0) / Jk
                diff = Yk - Y_mean
                sigma2[k, :] = (Jk / (Jk + weights[k])) * np.outer(diff, diff).flatten()
            else:
                Yk = Y[k, 0]  # Extract scalar
                Yneighbors = Y[ind, 0]  # Extract 1D array
                Y_mean = np.sum(weights[ind] * Yneighbors) / Jk
                diff = Yk - Y_mean
                sigma2[k, 0] = (Jk / (Jk + weights[k])) * diff**2

    return sigma2.squeeze()


def moulton(u: np.ndarray, clusterid: np.ndarray) -> float:
    """
    Moulton estimate of rho.

    Parameters
    ----------
    u : np.ndarray
        Residuals.
    clusterid : np.ndarray
        Cluster identifiers.

    Returns
    -------
    float
        Estimate of rho, or 0 if no clustering effect.
    """
    u = np.atleast_2d(u)
    if u.shape[1] > u.shape[0]:
        u = u.T

    # Group sizes
    unique_clusters, counts = np.unique(clusterid, return_counts=True)
    cluster_sizes_sq = np.sum(counts**2)
    den = cluster_sizes_sq - len(clusterid)

    if den > 0:
        # Sum of u within each cluster
        us = np.zeros((len(unique_clusters), u.shape[1]))
        for i, c in enumerate(unique_clusters):
            mask = clusterid == c
            us[i, :] = np.sum(u[mask, :], axis=0)

        # Cross product of cluster sums minus cross product of individual obs
        rho = (np.sum(us**2, axis=0) - np.sum(u**2, axis=0)) / den
        return rho if len(rho) > 1 else rho[0]
    else:
        return 0.0


def rot_bw(d: RDData, kern: str = "triangular") -> float:
    """
    Rule of thumb bandwidth for inference at a point.

    Parameters
    ----------
    d : RDData
        RD data object.
    kern : str
        Kernel type.

    Returns
    -------
    float
        Rule-of-thumb bandwidth.
    """
    X = d.X.flatten()
    Y = d.Y.flatten() if d.Y.ndim > 1 else d.Y
    N = len(X)
    order = 1

    # Determine if at boundary
    boundary = (np.min(X) >= 0) or (np.max(X) <= 0)

    # STEP 0: Estimate f_X(0) using Silverman
    iqr = np.percentile(X, 75) - np.percentile(X, 25)
    h1 = 1.843 * min(np.std(X), iqr / 1.349) / N**(1/5)
    f0 = np.sum(np.abs(X) <= h1) / (2 * N * h1)

    # STEP 1: Estimate (p+1)th derivative and sigma^2 using global polynomial
    Z = np.column_stack([X**p for p in range(order + 4)])
    coeffs = np.linalg.lstsq(Z, Y, rcond=None)[0]
    deriv = coeffs[order + 1]
    residuals = Y - Z @ coeffs
    sigma2 = np.var(residuals, ddof=len(coeffs))

    # STEP 2: Kernel constants
    s = get_kernel_constants(kern, order, boundary)
    nu0 = s["nu0"]
    mup = s.get(f"mu{order+1}", 0)

    # STEP 3: Plug in
    B = deriv * mup
    V = sigma2 * nu0 / f0

    if B == 0:
        return max(np.abs(X))

    return (V / (B**2 * 2 * (order + 1) * N))**(1 / (2 * order + 3))


def ik_bw(d: RDData, kern: str = "triangular", verbose: bool = False) -> float:
    """
    Imbens and Kalyanaraman bandwidth selector.

    Parameters
    ----------
    d : RDData
        RD data object (must be SRD).
    kern : str
        Kernel type.
    verbose : bool
        Print detailed output.

    Returns
    -------
    float
        IK bandwidth.
    """
    Nm = np.sum(d.m)
    Np = np.sum(d.p)
    N = Nm + Np
    X = d.X.flatten()
    Y = d.Y.flatten() if d.Y.ndim > 1 else d.Y

    # STEP 0: Kernel constant
    s = get_kernel_constants(kern, 1, True)
    const = (s["nu0"] / s["mu2"]**2)**(1/5)

    # STEP 1: Estimate f(0), sigma^2, using Silverman pilot bandwidth
    h1 = 1.84 * np.std(X) / N**(1/5)
    f0 = np.sum(np.abs(X) <= h1) / (2 * N * h1)

    # Preliminary variance estimation
    d_prelim = prelim_var(d, se_initial="Silverman")
    varm = d_prelim.sigma2[d.m][0] if hasattr(d_prelim.sigma2, '__getitem__') else d_prelim.sigma2
    varp = d_prelim.sigma2[d.p][0] if hasattr(d_prelim.sigma2, '__getitem__') else d_prelim.sigma2

    # STEP 2: Estimate second derivatives
    # Estimate third derivative using 3rd order polynomial
    mask = np.ones(N, dtype=bool)
    indicator = (X >= 0).astype(float)
    Z = np.column_stack([indicator, X, X**2, X**3])
    coeffs = np.linalg.lstsq(np.column_stack([np.ones(N), Z]), Y, rcond=None)[0]
    m3 = 6 * coeffs[4]

    # Left and right bandwidths
    if m3 == 0:
        h2m = h2p = h1
    else:
        h2m = 7200**(1/7) * (varm / (f0 * m3**2))**(1/7) * Nm**(-1/7)
        h2p = 7200**(1/7) * (varp / (f0 * m3**2))**(1/7) * Np**(-1/7)

    # Estimate second derivatives by local quadratic
    mask_m = (X >= -h2m) & (X < 0)
    mask_p = (X <= h2p) & (X >= 0)

    if np.sum(mask_m) >= 3:
        Zm = np.column_stack([np.ones(np.sum(mask_m)), X[mask_m], X[mask_m]**2])
        coeffs_m = np.linalg.lstsq(Zm, Y[mask_m], rcond=None)[0]
        m2m = 2 * coeffs_m[2]
    else:
        m2m = 0

    if np.sum(mask_p) >= 3:
        Zp = np.column_stack([np.ones(np.sum(mask_p)), X[mask_p], X[mask_p]**2])
        coeffs_p = np.linalg.lstsq(Zp, Y[mask_p], rcond=None)[0]
        m2p = 2 * coeffs_p[2]
    else:
        m2p = 0

    # STEP 3: Calculate regularization terms
    rm = 2160 * varm / (np.sum(mask_m) * h2m**4) if np.sum(mask_m) > 0 and h2m > 0 else 0
    rp = 2160 * varp / (np.sum(mask_p) * h2p**4) if np.sum(mask_p) > 0 and h2p > 0 else 0

    if verbose:
        print(f"h1: {h1}")
        print(f"N_-, N_+: {Nm}, {Np}")
        print(f"f(0): {f0}")
        print(f"sigma^2_+(0): {np.sqrt(varp)}^2")
        print(f"sigma^2_-(0): {np.sqrt(varm)}^2")
        print(f"m3: {m3}")
        print(f"h_2,+: {h2p}, h_2,-: {h2m}")
        print(f"m^(2)_+: {m2p}, m^(2)_-: {m2m}")
        print(f"r_+: {rp}, r_-: {rm}")

    # Final bandwidth
    denom = f0 * N * ((m2p - m2m)**2 + rm + rp)
    if denom <= 0:
        return np.max(np.abs(X))

    return const * ((varp + varm) / denom)**(1/5)


def prelim_var(d: RDData, se_initial: str = "EHW") -> RDData:
    """
    Compute preliminary variance estimate.

    Parameters
    ----------
    d : RDData
        RD data object.
    se_initial : str
        Method: "EHW" or "Silverman".

    Returns
    -------
    RDData
        Data object with sigma2 filled in.
    """
    from .npr import np_reg

    X = d.X.flatten()
    Y = d.Y

    # Determine minimum bandwidth
    if isinstance(d, IPData):
        unique_abs = np.sort(np.unique(np.abs(X)))
        sorted_abs = np.sort(np.abs(X))
        hmin = max(unique_abs[1] if len(unique_abs) > 1 else 0,
                   sorted_abs[3] if len(sorted_abs) > 3 else sorted_abs[-1])
    else:
        unique_p = np.sort(np.unique(X[d.p]))
        unique_m = np.sort(np.unique(np.abs(X[d.m])))
        sorted_p = np.sort(X[d.p])
        sorted_m = np.sort(np.abs(X[d.m]))

        hmin = max(
            unique_p[2] if len(unique_p) > 2 else (unique_p[-1] if len(unique_p) > 0 else 0),
            unique_m[2] if len(unique_m) > 2 else (unique_m[-1] if len(unique_m) > 0 else 0),
            sorted_p[3] if len(sorted_p) > 3 else (sorted_p[-1] if len(sorted_p) > 0 else 0),
            sorted_m[3] if len(sorted_m) > 3 else (sorted_m[-1] if len(sorted_m) > 0 else 0),
        )

    # Use reduced form for FRD
    d_rf = d
    if isinstance(d, FRDData):
        # Create a copy with only the first outcome column
        d_rf = SRDData(
            X=d.X, Y=d.Y[:, 0:1], orig_cutoff=d.orig_cutoff,
            p=d.p, m=d.m, weights=d.weights,
            clusterid=d.clusterid, covs=d.covs
        )

    if se_initial == "EHW":
        if isinstance(d, IPData):
            h1 = rot_bw(d_rf)
        else:
            h1 = ik_bw(d_rf)

        if np.isnan(h1):
            warnings.warn("Preliminary bandwidth is NaN, setting it to Inf")
            h1 = np.inf

        r1 = np_reg(d, max(h1, hmin), se_method="EHW")

    elif se_initial == "Silverman":
        # Silverman only for SRD/IK
        h1 = max(1.84 * np.std(X) / len(X)**(1/5), hmin)
        r1 = np_reg(d, h1, kern="uniform", order=0, se_method="EHW")

        # Variance adjustment for backward compatibility
        est_w = r1['est_w']
        if 'sigma2' in r1 and r1['sigma2'] is not None:
            sigma2 = r1['sigma2']
            mask_p = d.p & (est_w != 0)
            mask_m = d.m & (est_w != 0)
            lp = np.sum(mask_p)
            lm = np.sum(mask_m)
            if lp > 1:
                sigma2[d.p] = sigma2[d.p] * lp / (lp - 1)
            if lm > 1:
                sigma2[d.m] = sigma2[d.m] * lm / (lm - 1)
            r1['sigma2'] = sigma2
    else:
        raise ValueError(f"Unsupported se_initial method: {se_initial}")

    # Handle clustering
    if d.clusterid is not None:
        residuals = r1.get('residuals')
        if residuals is not None:
            mask = r1['est_w'] != 0
            d.rho = moulton(residuals[mask], d.clusterid[mask])

    # Compute variance
    est_w = r1['est_w']
    sigma2 = r1.get('sigma2')

    if sigma2 is not None:
        if isinstance(d, IPData):
            mask = est_w != 0
            d.sigma2 = np.full(len(X), np.mean(sigma2[mask]) if np.any(mask) else 0)
        elif isinstance(d, SRDData):
            mask_p = d.p & (est_w != 0)
            mask_m = d.m & (est_w != 0)
            mean_p = np.mean(sigma2[mask_p]) if np.any(mask_p) else 0
            mean_m = np.mean(sigma2[mask_m]) if np.any(mask_m) else 0
            d.sigma2 = mean_p * d.p + mean_m * d.m
        else:  # FRD
            mask_p = d.p & (est_w != 0)
            mask_m = d.m & (est_w != 0)
            if sigma2.ndim > 1:
                mean_p = np.mean(sigma2[mask_p], axis=0) if np.any(mask_p) else np.zeros(sigma2.shape[1])
                mean_m = np.mean(sigma2[mask_m], axis=0) if np.any(mask_m) else np.zeros(sigma2.shape[1])
                d.sigma2 = np.outer(d.p, mean_p) + np.outer(d.m, mean_m)
            else:
                mean_p = np.mean(sigma2[mask_p]) if np.any(mask_p) else 0
                mean_m = np.mean(sigma2[mask_m]) if np.any(mask_m) else 0
                d.sigma2 = mean_p * d.p + mean_m * d.m

    return d
