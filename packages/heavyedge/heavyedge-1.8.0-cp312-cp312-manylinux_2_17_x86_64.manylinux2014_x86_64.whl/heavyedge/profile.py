"""Various functions for edge profiles."""

__all__ = [
    "preprocess",
    "fill_after",
]


import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.stats import linregress


def preprocess(Ys, sigma, std_thres):
    """Preprocess raw profiles.

    Parameters
    ----------
    Ys : (N, M) array
        Array of N profiles.
    sigma : scalar
        Standard deviation of Gaussian filter for smoothing.
    std_thres : scalar
        Standard deviation threshold to detect contact point.

    Returns
    -------
    Ys : (N, M) array
        Preprocessed profile data.
    Ls : (N,) array
        Length of *Y* until the contact point.

    Notes
    -----
    Profiles undergo the following steps:

    1. Profile direction is set so that the contact point is on the right hand side.
    2. Contact point is detected, and set to have zero height.

    Examples
    --------
    >>> import numpy as np
    >>> from heavyedge import get_sample_path, RawProfileCsvs
    >>> from heavyedge.profile import preprocess
    >>> raw = RawProfileCsvs(get_sample_path("Type3"))
    >>> Ys = np.array([raw[i][0] for i in range(len(raw))])
    >>> Ys_processed, Ls = preprocess(Ys, 32, 0.01)
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... for Y, L in zip(Ys_processed, Ls):
    ...     plt.plot(Y[:L])
    """
    ret_Ys, ret_Ls = [], []
    for Y in Ys:
        Y_proc, L = _preprocess(Y, sigma, std_thres)
        ret_Ys.append(Y_proc)
        ret_Ls.append(L)
    return np.array(ret_Ys), np.array(ret_Ls)


def _preprocess(Y, sigma, std_thres):
    if Y[0] < Y[-1]:
        # Make plateau is on the left and cp is on the right
        Y = np.flip(Y)

    X = np.arange(len(Y))
    h_xx = gaussian_filter1d(Y, sigma, order=2, mode="nearest")
    if len(h_xx) > 0:
        peaks, _ = find_peaks(h_xx)
    else:
        peaks = np.empty(0, dtype=int)

    candidates = []
    for i, peak_idx in enumerate(peaks):
        x = X[peak_idx:]
        if not len(x) > 2:
            continue
        y = Y[x]
        reg = linregress(x, y)
        residuals = y - (reg.intercept + reg.slope * x)
        std = np.sqrt(np.sum(residuals**2) / (len(x) - 2))
        if std < std_thres:
            candidates.append(i)

    if candidates:
        cp = peaks[candidates[np.argmax(h_xx[peaks[candidates]])]]
    else:
        cp = len(Y) - 1

    # If any point before cp is lower than the detected contact point,
    # set that as contact point instead.
    cp = np.argmin(Y[: cp + 1])
    Y = Y - Y[cp]
    return Y, cp + 1


def fill_after(Ys, Ls, fill_value):
    """Fill arrays with a constant value after specified lengths.

    The input array *Ys* is modified.

    Parameters
    ----------
    Ys : (N, M) array
        Array of N profiles.
    Ls : (N,) array
        Length of each profile.
    fill_value : scalar
        Value to fill *Ys*.

    Examples
    --------
    >>> from heavyedge import get_sample_path, ProfileData
    >>> from heavyedge.profile import fill_after
    >>> with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    ...     x = data.x()
    ...     Ys, Ls, _ = data[:]
    >>> fill_after(Ys, Ls, float("nan"))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... plt.plot(Ys.T)
    """
    _, M = Ys.shape
    Ys[np.arange(M)[None, :] >= Ls[:, None]] = fill_value
