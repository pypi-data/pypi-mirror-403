"""
Plotting functions for RDHonest.
"""

import numpy as np
import pandas as pd
from typing import Optional, Union

from .utils import create_rd_data


def rd_scatter(
    Y: np.ndarray,
    X: np.ndarray,
    cutoff: float = 0.0,
    avg: Union[int, float] = 10,
    xlab: Optional[str] = None,
    ylab: Optional[str] = None,
    vert: bool = True,
    propdotsize: bool = False,
    ax=None,
    **kwargs
):
    """
    Scatterplot of binned raw observations.

    Creates a scatterplot where each point corresponds to a binned average.

    Parameters
    ----------
    Y : np.ndarray
        Outcome variable.
    X : np.ndarray
        Running variable.
    cutoff : float
        RD cutoff for the running variable.
    avg : int or float
        Number of observations to average over. If Inf, take averages
        for each unique value of X (good for discrete X).
    xlab : str, optional
        X-axis label.
    ylab : str, optional
        Y-axis label.
    vert : bool
        Draw vertical line at cutoff?
    propdotsize : bool
        If True, point size proportional to number of observations.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on. If None, creates new figure.
    **kwargs
        Additional arguments passed to scatter plot.

    Returns
    -------
    matplotlib.axes.Axes
        The plot axes.

    Examples
    --------
    >>> rd_scatter(log_earnings, yearat14, cutoff=1947, avg=np.inf, propdotsize=True)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for plotting. "
                         "Install with: pip install matplotlib")

    Y = np.asarray(Y).flatten()
    X = np.asarray(X).flatten()

    # Create data object
    d = create_rd_data(Y=Y, X=X, cutoff=cutoff, method="SRD")
    x_centered = d.X.flatten()

    if avg == np.inf or avg == float('inf'):
        # Average for each unique value
        unique_x = np.unique(x_centered)
        bd_x = []
        bd_y = []
        bd_count = []
        for xu in unique_x:
            mask = x_centered == xu
            bd_x.append(xu)
            bd_y.append(np.mean(Y[np.argsort(X - cutoff)][mask]))
            bd_count.append(np.sum(mask))
        bd = pd.DataFrame({'x': bd_x, 'y': bd_y, 'count': bd_count})
    else:
        avg = int(avg)
        # Bin observations
        Y_sorted = d.Y.flatten()

        # Below cutoff (negative X)
        idx_m = np.where(d.m)[0]
        nm = len(idx_m)
        maxm = (nm // avg) * avg

        # Above cutoff (positive X)
        idx_p = np.where(d.p)[0]
        np_ = len(idx_p)
        maxp = (np_ // avg) * avg

        bd_x = []
        bd_y = []

        # Process below cutoff
        if maxm > 0:
            x_m = x_centered[idx_m[:maxm]].reshape(-1, avg)
            y_m = Y_sorted[idx_m[:maxm]].reshape(-1, avg)
            bd_x.extend(np.mean(x_m, axis=1))
            bd_y.extend(np.mean(y_m, axis=1))

        # Remainder below
        if maxm < nm:
            bd_x.append(np.mean(x_centered[idx_m[maxm:]]))
            bd_y.append(np.mean(Y_sorted[idx_m[maxm:]]))

        # Process above cutoff
        if maxp > 0:
            x_p = x_centered[idx_p[:maxp]].reshape(-1, avg)
            y_p = Y_sorted[idx_p[:maxp]].reshape(-1, avg)
            bd_x.extend(np.mean(x_p, axis=1))
            bd_y.extend(np.mean(y_p, axis=1))

        # Remainder above
        if maxp < np_:
            bd_x.append(np.mean(x_centered[idx_p[maxp:]]))
            bd_y.append(np.mean(Y_sorted[idx_p[maxp:]]))

        bd = pd.DataFrame({'x': bd_x, 'y': bd_y, 'count': [avg] * len(bd_x)})

    # Add back original cutoff
    bd['x'] = bd['x'] + cutoff

    # Create plot
    if ax is None:
        fig, ax = plt.subplots()

    if propdotsize:
        sizes = bd['count'] * 10  # Scale factor
        ax.scatter(bd['x'], bd['y'], s=sizes, **kwargs)
    else:
        ax.scatter(bd['x'], bd['y'], **kwargs)

    if xlab is not None:
        ax.set_xlabel(xlab)
    if ylab is not None:
        ax.set_ylabel(ylab)

    if vert:
        ax.axvline(x=cutoff, linestyle=':', color='gray')

    return ax


def RDScatter(
    formula: Optional[str] = None,
    data: Optional[pd.DataFrame] = None,
    Y: Optional[np.ndarray] = None,
    X: Optional[np.ndarray] = None,
    cutoff: float = 0.0,
    avg: Union[int, float] = 10,
    xlab: Optional[str] = None,
    ylab: Optional[str] = None,
    vert: bool = True,
    propdotsize: bool = False,
    subset: Optional[np.ndarray] = None,
    ax=None,
    **kwargs
):
    """
    R-style interface for rd_scatter.

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
    avg : int or float
        Binning parameter.
    xlab : str, optional
        X-axis label.
    ylab : str, optional
        Y-axis label.
    vert : bool
        Draw vertical line?
    propdotsize : bool
        Proportional dot sizes?
    subset : np.ndarray, optional
        Boolean subset.
    ax : matplotlib.axes.Axes, optional
        Axes to plot on.
    **kwargs
        Additional scatter arguments.

    Returns
    -------
    matplotlib.axes.Axes
        The plot.
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
    elif Y is None or X is None:
        raise ValueError("Must provide either (formula, data) or (Y, X)")

    return rd_scatter(
        Y=Y, X=X, cutoff=cutoff, avg=avg,
        xlab=xlab, ylab=ylab, vert=vert, propdotsize=propdotsize,
        ax=ax, **kwargs
    )
