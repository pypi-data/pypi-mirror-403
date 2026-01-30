"""
Kernel functions for local polynomial regression.
"""

import numpy as np
from scipy import integrate


def eq_kern(kernel: str = "uniform", boundary: bool = True, order: int = 0):
    """
    Equivalent kernel for local polynomial regression.

    Parameters
    ----------
    kernel : str or callable
        Kernel type. One of "triangular", "epanechnikov", "uniform",
        or a kernel function.
    boundary : bool
        Whether we are at a boundary.
    order : int
        Order of local polynomial (0=constant, 1=linear, 2=quadratic).

    Returns
    -------
    callable
        Equivalent kernel function.
    """
    def su(u):
        """Support function."""
        lower = 0 if boundary else -1
        return (u <= 1) & (u >= lower)

    if callable(kernel):
        return eq_kern_numerical(kernel, boundary=boundary, order=order)
    elif order > 2:
        K = eq_kern(kernel=kernel, boundary=boundary, order=0)
        return eq_kern_numerical(K, boundary=boundary, order=order)
    else:
        key = f"{order}{boundary}{kernel}"
        kernels = {
            # Order 0, interior (boundary=False)
            "0Falseuniform": lambda u: np.where(su(u), 0.5, 0),
            "0Falsetriangular": lambda u: np.where(su(u), 1 - np.abs(u), 0),
            "0Falseepanechnikov": lambda u: np.where(su(u), 0.75 * (1 - u**2), 0),
            # Order 0, boundary (boundary=True)
            "0Trueuniform": lambda u: np.where(su(u), 1.0, 0),
            "0Truetriangular": lambda u: np.where(su(u), 2 * (1 - u), 0),
            "0Trueepanechnikov": lambda u: np.where(su(u), 1.5 * (1 - u**2), 0),
            # Order 1, interior
            "1Falseuniform": lambda u: np.where(su(u), 0.5, 0),
            "1Falsetriangular": lambda u: np.where(su(u), 1 - np.abs(u), 0),
            "1Falseepanechnikov": lambda u: np.where(su(u), 0.75 * (1 - u**2), 0),
            # Order 1, boundary
            "1Trueuniform": lambda u: np.where(su(u), 4 - 6*u, 0),
            "1Truetriangular": lambda u: np.where(su(u), 6 * (1 - 2*u) * (1 - u), 0),
            "1Trueepanechnikov": lambda u: np.where(su(u), 6/19 * (16 - 30*u) * (1 - u**2), 0),
            # Order 2, interior
            "2Falseuniform": lambda u: np.where(su(u), (9 - 15*u**2) / 8, 0),
            "2Falsetriangular": lambda u: np.where(su(u), 6/7 * (2 - 5*u**2) * (1 - np.abs(u)), 0),
            "2Falseepanechnikov": lambda u: np.where(su(u), 15/32 * (3 - 7*u**2) * (1 - u**2), 0),
            # Order 2, boundary
            "2Trueuniform": lambda u: np.where(su(u), 9 - 36*u + 30*u**2, 0),
            "2Truetriangular": lambda u: np.where(su(u), 12 * (1 - 5*u + 5*u**2) * (1 - u), 0),
            "2Trueepanechnikov": lambda u: np.where(su(u), 1/8 * (85 - 400*u + 385*u**2) * (1 - u**2), 0),
        }
        return kernels.get(key, lambda u: np.zeros_like(np.asarray(u, dtype=float)))


def kern_moment(K, moment: int = 0, boundary: bool = True, type_: str = "raw") -> float:
    """
    Compute moments of a kernel.

    Parameters
    ----------
    K : callable
        Kernel function.
    moment : int
        Order of moment to compute.
    boundary : bool
        If True, integrate over [0, 1]; otherwise [-1, 1].
    type_ : str
        "raw" for integral of u^j * K(u),
        "absolute" for integral of |u^j * K(u)|,
        "raw2" for integral of u^j * K(u)^2.

    Returns
    -------
    float
        The moment value.
    """
    lower = 0 if boundary else -1

    if type_ == "raw":
        fkt = lambda u: u**moment * K(u)
    elif type_ == "absolute":
        fkt = lambda u: np.abs(u**moment * K(u))
    elif type_ == "raw2":
        fkt = lambda u: u**moment * K(u)**2
    else:
        raise ValueError(f"Unknown type: {type_}")

    result, _ = integrate.quad(fkt, lower, 1, epsrel=np.finfo(float).eps**0.75)
    return result


def kern_matrix(K, order: int = 2, boundary: bool = True) -> np.ndarray:
    """
    Compute kernel M matrix.

    Parameters
    ----------
    K : callable
        Kernel function.
    order : int
        Polynomial order.
    boundary : bool
        Boundary or interior.

    Returns
    -------
    np.ndarray
        The M matrix.
    """
    M = np.zeros((order + 1, order + 1))
    for i in range(order + 1):
        for j in range(order + 1):
            M[i, j] = kern_moment(K, moment=i+j, boundary=boundary)
    return M


def eq_kern_numerical(K, boundary: bool = True, order: int = 0):
    """
    Compute equivalent kernel numerically.

    Parameters
    ----------
    K : callable
        Base kernel function.
    boundary : bool
        Boundary or interior.
    order : int
        Polynomial order.

    Returns
    -------
    callable
        Equivalent kernel function.
    """
    M = kern_matrix(K, order=order, boundary=boundary)
    s = np.linalg.solve(M, np.eye(order + 1))[0, :]

    def eq_kern_func(u):
        u = np.atleast_1d(u)
        result = np.zeros_like(u, dtype=float)
        for j, coef in enumerate(s):
            result += coef * u**j
        return result * K(u)

    return eq_kern_func


# Precomputed kernel constants (equivalent to kernC in R)
KERNEL_CONSTANTS = {
    # (kernel, order, boundary): {nu0, mu1, mu2, ...}
    ("triangular", 1, True): {"nu0": 4.8, "mu1": 1/6, "mu2": 1/12},
    ("triangular", 1, False): {"nu0": 0.6666667, "mu1": 0, "mu2": 1/6},
    ("epanechnikov", 1, True): {"nu0": 2.7315789, "mu1": 3/16, "mu2": 1/10},
    ("epanechnikov", 1, False): {"nu0": 0.6, "mu1": 0, "mu2": 1/5},
    ("uniform", 1, True): {"nu0": 5.333333, "mu1": 1/4, "mu2": 1/6},
    ("uniform", 1, False): {"nu0": 0.5, "mu1": 0, "mu2": 1/3},
    ("triangular", 0, True): {"nu0": 1.333333, "mu1": 1/3},
    ("triangular", 0, False): {"nu0": 0.6666667, "mu1": 0},
    ("epanechnikov", 0, True): {"nu0": 1.2, "mu1": 3/8},
    ("epanechnikov", 0, False): {"nu0": 0.6, "mu1": 0},
    ("uniform", 0, True): {"nu0": 1, "mu1": 1/2},
    ("uniform", 0, False): {"nu0": 0.5, "mu1": 0},
}


def get_kernel_constants(kernel: str, order: int, boundary: bool) -> dict:
    """
    Get precomputed kernel constants.

    Parameters
    ----------
    kernel : str
        Kernel type.
    order : int
        Polynomial order.
    boundary : bool
        Boundary or interior.

    Returns
    -------
    dict
        Dictionary with kernel constants.
    """
    key = (kernel, order, boundary)
    if key in KERNEL_CONSTANTS:
        return KERNEL_CONSTANTS[key]
    else:
        # Compute numerically
        K = eq_kern(kernel, boundary=False, order=0)
        Keq = eq_kern(kernel, boundary=boundary, order=order)
        nu0 = kern_moment(Keq, moment=0, boundary=boundary, type_="raw2")
        result = {"nu0": nu0}
        for p in range(1, order + 2):
            result[f"mu{p}"] = kern_moment(Keq, moment=p, boundary=boundary, type_="raw")
        return result


def triangular_kernel(u):
    """Triangular kernel: (1 - |u|)+"""
    return np.maximum(1 - np.abs(u), 0)


def epanechnikov_kernel(u):
    """Epanechnikov kernel: (3/4)(1 - u^2)+"""
    return np.where(np.abs(u) <= 1, 0.75 * (1 - u**2), 0)


def uniform_kernel(u):
    """Uniform kernel: (|u| < 1) / 2"""
    return np.where(np.abs(u) < 1, 0.5, 0)


def get_kernel_function(kern: str):
    """
    Get kernel function from string.

    Parameters
    ----------
    kern : str
        Kernel type.

    Returns
    -------
    callable
        Kernel function.
    """
    kernels = {
        "triangular": triangular_kernel,
        "epanechnikov": epanechnikov_kernel,
        "uniform": uniform_kernel,
    }
    if kern in kernels:
        return kernels[kern]
    elif callable(kern):
        return kern
    else:
        raise ValueError(f"Unknown kernel: {kern}")
