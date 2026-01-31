"""Profile preprocessing."""

import numpy as np

from heavyedge.profile import fill_after, preprocess

__all__ = [
    "prep",
    "fill",
]


def prep(
    raw_file,
    sigma,
    std_thres,
    fill_value=0.0,
    z_thres=None,
    batch_size=None,
    logger=lambda x: None,
):
    """Preprocess raw profiles in the given file.

    Parameters
    ----------
    raw_file : heavyedge.RawProfileBase
        Opened raw profile file.
    sigma : scalar
        Standard deviation of Gaussian filter for smoothing.
    std_thres : scalar
        Standard deviation threshold to detect contact point.
    fill_value : scalar, default=0.0
        Value to fill after the contact point.
        If None, does not fill the array.
    z_thres : scalar, optional
        Z-score threshold to detect outliers.
        If not passed, outlier detection is not performed.
    batch_size : int, optional
        Batch size to load data.
        If not passed, all data are loaded at once.
    logger : callable, optional
        Logger function which accepts a progress message string.

    Yields
    ------
    Y_processed : (batch_size, M) array
        Preprocessed profiles.
    Ls : (batch_size,) array
        Lengths of the preprocessed profiles.
    names : (batch_size,) array
        Names of the preprocessed profiles.

    Examples
    --------
    >>> from heavyedge import get_sample_path, RawProfileCsvs
    >>> from heavyedge.api import prep
    >>> raw = RawProfileCsvs(get_sample_path("Type3"))
    >>> Ys, Ls, _ = next(prep(raw, 32, 0.01, batch_size=3))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... for Y, L in zip(Ys, Ls):
    ...     plt.plot(Y[:L])
    """
    if z_thres is not None:
        gen = _prep_outlier(raw_file, sigma, std_thres, z_thres)
    else:
        gen = _prep(raw_file, sigma, std_thres)

    N = len(raw_file)
    batch_count = 0
    Ys, Ls, names = [], [], []
    for i, (Y, L, name) in enumerate(gen):
        if fill_value is not None:
            Y[L:] = fill_value
        Ys.append(Y)
        Ls.append(L)
        names.append(name)
        batch_count += 1

        if batch_count == batch_size:
            logger(f"{i}/{N}")
            yield Ys, Ls, names
            Ys, Ls, names = [], [], []
            batch_count = 0

    # yield remaining batch
    logger(f"{N}/{N}")
    yield Ys, Ls, names


def _prep_outlier(raw, sigma, std_thres, z_thres):
    idxs, Ls, sums = [], [], []
    for i in range(len(raw)):
        Y, _ = raw[i]
        if _is_invalid(Y):
            continue
        (Y,), (L,) = preprocess(Y.reshape(1, -1), sigma, std_thres)
        idxs.append(i)
        Ls.append(L)
        sums.append(np.sum(Y[:L]))
    sums = np.array(sums)
    is_outlier = _outlier(sums, z_thres)
    idxs = np.array(idxs)[~is_outlier]
    Ls = np.array(Ls)[~is_outlier]

    # yield
    for i, L in zip(idxs, Ls):
        Y, name = raw[i]
        if Y[0] < Y[-1]:
            Y = np.flip(Y)
        Y = Y - Y[L - 1]
        yield Y, L, name


def _outlier(values, thres=3.5):
    # Boris Iglewicz and David C Hoaglin,
    # Volume 16: how to detect and handle outliers. Quality Press, 1993.
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    mod_z = 0.6745 * (values - med) / mad
    return np.abs(mod_z) > thres


def _prep(raw, sigma, std_thres):
    for i in range(len(raw)):
        Y, name = raw[i]
        if _is_invalid(Y):
            continue
        (Y,), (L,) = preprocess(Y.reshape(1, -1), sigma, std_thres)
        yield Y, L, name


def _is_invalid(profile):
    return (len(profile) == 0) or np.any(np.isnan(profile)) or np.any(np.isinf(profile))


def fill(file, fill_value, batch_size=None, logger=lambda x: None):
    """Fill profiles after the contact point.

    Parameters
    ----------
    file : heavyedge.ProfileData
        Open h5 file.
    fill_value : scalar
        Value to fill after the contact point.
    batch_size : int, optional
        Batch size to load data.
        If not passed, all data are loaded at once.
    logger : callable, optional
        Logger function which accepts a progress message string.

    Yields
    ------
    Ys : (batch_size, M) array
        Filled profiles.
    Ls : (batch_size,) array
        Lengths of the filled profiles.
    names : (batch_size,) array
        Names of the filled profiles.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.api import fill
    >>> with ProfileData(get_sample_path("Prep-Type1.h5")) as file:
    ...     Ys, _, _ = file[:]
    ...     Ys_filled, _, _ = next(fill(file, float("nan")))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(Ys.T, color="gray")
    ... plt.plot(Ys_filled.T)
    """
    N = len(file)
    if batch_size is None:
        Ys, Ls, names = file[:]
        fill_after(Ys, Ls, fill_value)
        logger(f"{N}/{N}")
        yield Ys, Ls, names
    else:
        for i in range(0, N, batch_size):
            Ys, Ls, names = file[i : i + batch_size]
            fill_after(Ys, Ls, fill_value)
            logger(f"{i}/{N}")
            yield Ys, Ls, names
