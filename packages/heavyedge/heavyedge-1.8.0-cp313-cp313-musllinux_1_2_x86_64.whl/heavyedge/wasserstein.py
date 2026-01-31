"""
Wasserstein distance
--------------------

Wasserstein-related functions.
"""

import warnings

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d

from ._wasserstein import _optimize_q, _quantile

__all__ = [
    "quantile",
    "wdist",
    "wmean",
]


def _deprecated(version, replace):
    removed_version = str(int(version.split(".")[0]) + 1) + ".0"

    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__}() is deprecated since HeavyEdge {version} "
                f"and will be removed in {removed_version}. "
                f"Use {replace} instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def quantile(x, fs, Ls, t):
    """Convert probability distributions to quantile functions.

    Parameters
    ----------
    x : (M1,) ndarray
        Coordinates of grids over which *fs* are measured.
    fs : (N, M1) ndarray
        Empirical probability density functions.
        Each function must have zero values after each length in *Ls*.
    Ls : (N,) ndarray
        Length of supports of each *fs*.
    t : (M2,) ndarray
        Points over which the quantile function will be measured.
        Must be strictly increasing from 0 to 1.

    Returns
    -------
    (N, M2) ndarray
        Quantile functions* over *t*.

    Examples
    --------
    >>> import numpy as np
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.wasserstein import quantile
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> fs = Ys / np.trapezoid(Ys, x, axis=-1)[:, np.newaxis]
    >>> t = np.linspace(0, 1, 100)
    >>> Qs = quantile(x, fs, Ls, t)
    """
    Gs = cumulative_trapezoid(fs, x, initial=0, axis=-1)
    return _quantile(x, Gs, Ls.astype(np.int32), t)


def _quantile_old(x, f, t):
    G = cumulative_trapezoid(f, x, initial=0)
    return interp1d(G, x, bounds_error=False, fill_value=(x[0], x[-1]))(t)


@_deprecated("1.6", "HeavyEdge-Distance package")
def wdist(x1, f1, x2, f2, grid_num):
    r"""Wasserstein distance between two 1D probability distributions.

    .. deprecated:: 1.6
        This function will be removed in HeavyEdge 2.0.
        Use HeavyEdge-Distance package instead.

    .. math::

        d_W(f_1, f_2)^2 = \int^1_0 (Q_1(t) - Q_2(t))^2 dt

    where :math:`Q_i` is the quantile function of :math:`f_i`.

    Parameters
    ----------
    x1, f1 : ndarray
        The first empirical probability density function.
    x2, f2 : ndarray
        The second empirical probability density function.
    grid_num : int
        Number of sample points in [0, 1] to approximate the integral.

    Returns
    -------
    scalar
        Wasserstein distance.
    """
    grid = np.linspace(0, 1, grid_num)
    Q1 = _quantile_old(x1, f1, grid)
    Q2 = _quantile_old(x2, f2, grid)
    return np.trapezoid((Q1 - Q2) ** 2, grid) ** 0.5


def wmean(x, fs, Ls, t):
    """Fréchet mean of probability distrubutions using Wasserstein metric.

    Parameters
    ----------
    x : (M1,) ndarray
        Coordinates of grids over which *fs* are measured.
    fs : (N, M1) ndarray
        Empirical probability density functions.
        Each function must have zero values after each length in *Ls*.
    Ls : (N,) ndarray
        Length of supports of each *fs*.
    t : (M2,) ndarray
        Points over which the quantile function will be measured.
        Must be strictly increasing from 0 to 1.

    Returns
    -------
    f_mean : ndarray
        Fréchet mean of *fs* over *x*.
    L : int
        Length of the support of *f_mean*.

    Examples
    --------
    >>> import numpy as np
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.wasserstein import wmean
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> fs = Ys / np.trapezoid(Ys, x, axis=-1)[:, np.newaxis]
    >>> f_mean, L = wmean(x, fs, Ls, np.linspace(0, 1, 100))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(x, fs.T, "--", color="gray")
    ... plt.plot(x[:L], f_mean[:L])
    """
    Qs = quantile(x, fs, Ls, t)
    g = np.mean(Qs, axis=0)
    return _wmean(x, t, g)


def _wmean(x, t, g):
    if np.all(np.diff(g) >= 0):
        q = g
    else:
        q = _optimize_q(g)
    pdf = 1 / np.gradient(q, t)
    pdf[-1] = 0
    pdf /= np.trapezoid(pdf, q)

    L = np.searchsorted(x, q[-1]) + 1
    return np.interp(x, q, pdf, left=pdf[0], right=0), L


def _wmean_old(xs, fs, grid_num):
    grid = np.linspace(0, 1, grid_num)
    Q = np.array([_quantile_old(x, f, grid) for x, f in zip(xs, fs)])
    g = np.mean(Q, axis=0)
    if np.all(np.diff(g) >= 0):
        q = g
    else:
        q = _optimize_q(g)
    pdf = 1 / np.gradient(q, grid)
    pdf[-1] = 0
    pdf /= np.trapezoid(pdf, q)
    return q, pdf
