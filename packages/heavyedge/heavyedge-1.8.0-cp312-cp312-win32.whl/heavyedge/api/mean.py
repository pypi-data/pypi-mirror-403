"""Estimate average profiles."""

import warnings

import numpy as np

from heavyedge.wasserstein import _wmean, quantile, wmean

__all__ = [
    "mean_euclidean",
    "mean_wasserstein",
]


def mean_euclidean(f, batch_size=None, logger=lambda x: None):
    """Compute arithmetic mean profile.

    Parameters
    ----------
    f : heavyedge.ProfileData
        Open h5 file of profiles.
    batch_size : int, optional
        Batch size to load data.
        If not passed, all data are loaded at once.
    logger : callable, optional
        Logger function which accepts a progress message string.

    Returns
    -------
    (M,) array
        Average profile.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.api import mean_euclidean
    >>> with ProfileData(get_sample_path("Prep-Type3.h5")) as f:
    ...     Ys, _, _ = f[:]
    ...     mean = mean_euclidean(f, batch_size=5)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(Ys.T, "--", color="gray")
    ... plt.plot(mean)
    """
    N, M = f.shape()
    if batch_size is None:
        Ys, _, _ = f[:]
        mean = np.mean(Ys, axis=0, dtype=np.float64)
        logger(f"{N}/{N}")
    else:
        mean = np.zeros((M,), dtype=np.float64)

        for i in range(0, N, batch_size):
            Ys, _, _ = f[i : i + batch_size]
            mean += np.sum(Ys, axis=0)
            logger(f"{i}/{N}")
        mean /= N
    return mean


def mean_wasserstein(f, grid_num, batch_size=None, logger=lambda x: None):
    """Compute mean profile by Fréchet mean with respect to Wasserstein metric.

    Parameters
    ----------
    f : heavyedge.ProfileData
        Open h5 file of profiles.
    grid_num : int
        Number of grids to sample quantile functions.
    batch_size : int, optional
        Batch size to load data.
        If not passed, all data are loaded at once.
    logger : callable, optional
        Logger function which accepts a progress message string.

    Returns
    -------
    f_mean : (M,) array
        Average profile.
    L : int
        Length of the support of *f_mean*.

    Notes
    -----
    This function automatically fills the profiles with zero values after their contact
    points.
    In HeavyEdge 2.0, this feature will be removed and *f* will be required to contain
    profiles already filled with zero values.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.api import mean_wasserstein
    >>> with ProfileData(get_sample_path("Prep-Type3.h5")) as f:
    ...     Ys, _, _ = f[:]
    ...     mean, L = mean_wasserstein(f, 100)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(Ys.T, "--", color="gray")
    ... plt.plot(mean[:L])
    """
    x = f.x()
    t = np.linspace(0, 1, grid_num)

    N = len(f)
    DEPRECATED = False
    if batch_size is None:
        Ys, Ls, _ = f[:]
        # zero filling: will be removed in v2.0
        _, M = Ys.shape
        mask = np.arange(M)[None, :] >= Ls[:, None]
        if np.any(Ys[mask] != 0):
            DEPRECATED = True
            Ys[mask] = 0
        # zero filling complete.
        As = np.trapezoid(Ys, x, axis=-1)
        fs = Ys / As[:, np.newaxis]
        mean, L = wmean(x, fs, Ls, t)
        mean_A = As.mean()
        logger(f"{N}/{N}")
    else:
        g = np.zeros((grid_num,), dtype=np.float64)
        mean_A = 0

        for i in range(0, N, batch_size):
            Ys, Ls, _ = f[i : i + batch_size]
            # zero filling: will be removed in v2.0
            _, M = Ys.shape
            mask = np.arange(M)[None, :] >= Ls[:, None]
            if np.any(Ys[mask] != 0):
                DEPRECATED = True
                Ys[mask] = 0
            # zero filling complete.
            As = np.trapezoid(Ys, x, axis=-1)
            fs = Ys / As[:, np.newaxis]
            Qs = quantile(x, fs, Ls, t)
            g += np.sum(Qs, axis=0)
            mean_A += np.sum(As)
            logger(f"{i}/{N}")
        g /= N
        mean, L = _wmean(x, t, g)
        mean_A /= N

    if DEPRECATED:
        warnings.warn(
            "Passing profiles to mean_wasserstein() whose values after their "
            "contact points are not zero is deprecated and will be removed in v2.0",
            DeprecationWarning,
            stacklevel=2,
        )

    return mean * mean_A, L
