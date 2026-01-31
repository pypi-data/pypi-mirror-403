"""Raw profile data files."""

import abc
import csv
import warnings
from pathlib import Path

import numpy as np

__all__ = [
    "RawProfileBase",
    "RawProfileCsvs",
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


class RawProfileBase(abc.ABC):
    """Base class to read raw profile data.

    All profiles must have the same length.

    Notes
    -----
    ``self[key]`` returns a tuple of profile(s) and profile name(s).
    """

    def __init__(self, path):
        self.path = Path(path).expanduser()

    def __len__(self):
        """Return number of profile data.

        .. note::
            This method will be an abstract method in HeavyEdge 2.0.
            User should implement it with an efficient algorithm.
        """
        return self.count_profiles()

    def __getitem__(self, key):
        """Return profile and name at index.

        .. note::
            This method will be an abstract method in HeavyEdge 2.0.
            User should implement it with an efficient algorithm.
        """
        return (self.all_profiles()[key], np.array(self.profile_names())[key])

    @_deprecated("1.6", "__len__() method")
    @abc.abstractmethod
    def count_profiles(self):
        """Number of raw profiles.

        .. deprecated:: 1.6
            This method will be removed in HeavyEdge 2.0.
            Implement __len__() and use len() instead.

        Returns
        -------
        int
        """

    @_deprecated("1.6", "__getitem__() method")
    def profiles(self):
        """Yield raw profiles.

        .. deprecated:: 1.6
            This method will be removed in HeavyEdge 2.0.
            Implement __getitem__() and index the object instead.

        Yields
        ------
        1-D ndarray
        """

    @_deprecated("1.6", "__getitem__() method")
    @abc.abstractmethod
    def all_profiles(self):
        """Return all profiles as an 2-D array.

        .. deprecated:: 1.6
            This method will be removed in HeavyEdge 2.0.
            Implement __getitem__() and index the object instead.

        Returns
        -------
        2-D ndarray
        """
        return np.array([p for p in self.profiles()])

    @_deprecated("1.6", "__getitem__() method")
    @abc.abstractmethod
    def profile_names(self):
        """Yield profile names.

        .. deprecated:: 1.6
            This method will be removed in HeavyEdge 2.0.
            Implement __getitem__() and index the object instead.

        Yields
        ------
        str
        """


class RawProfileCsvs(RawProfileBase):
    """Read raw profile data from a directory containing CSV files.

    Directory structure:

    .. code-block::

        rawdata/
        ├── profile1.csv
        ├── profile2.csv
        └── ...

    Parameters
    ----------
    path : pathlike
        Path to the directory containing the raw CSV files.

    Notes
    -----
    - Each CSV file must contain a single column of numeric values (no header).
    - The order of profiles is determined by the sorted filenames.
    - The profile name is derived from the filename stem.

    Examples
    --------
    >>> from heavyedge import get_sample_path, RawProfileCsvs
    >>> profiles = RawProfileCsvs(get_sample_path("Type3"))
    >>> import matplotlib.pyplot as plt  # doctest: +SKIP
    ... for i in range(len(profiles)):
    ...     profile, _ = profiles[i]
    ...     plt.plot(profile)
    """

    def __init__(self, path):
        super().__init__(path)
        self._files = sorted(self.path.glob("*.csv"))

    def __len__(self):
        return len(self._files)

    @staticmethod
    def _read_profile(path):
        with open(path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            profile = np.array([float(row[0]) for row in reader])
        return profile

    def __getitem__(self, key):
        file = self._files[key]
        return (self._read_profile(file), str(file.stem))

    def count_profiles(self):
        # TODO: remove in HeavyEdge 2.0
        return len(self)

    def profiles(self):
        # TODO: remove in HeavyEdge 2.0
        for file in self._files:
            yield self._read_profile(file)

    def profile_names(self):
        # TODO: remove in HeavyEdge 2.0
        for f in self._files:
            yield str(f.stem)
