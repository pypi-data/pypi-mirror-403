import os
import subprocess

import numpy as np
import pytest

from heavyedge import ProfileData


def test_process_commands(tmp_rawdata_type2_path, tmp_path):
    processed_path = tmp_path / "ProcessedProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "prep",
            "--type",
            "csvs",
            "--res=1",
            "--sigma=1",
            "--std-thres=40",
            "--fill-value=0",
            "--z-thres=3.5",
            tmp_rawdata_type2_path,
            "-o",
            processed_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(processed_path)

    merged_path = tmp_path / "MergedProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "merge",
            processed_path,
            processed_path,
            "-o",
            merged_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(merged_path)

    with ProfileData(processed_path) as data:
        N = len(data)
    index_path = tmp_path / "index.npy"
    np.save(index_path, np.arange(N))
    filtered_path = tmp_path / "FilteredProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "filter",
            processed_path,
            index_path,
            "-o",
            filtered_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(filtered_path)

    filled_path = tmp_path / "FilledProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "fill",
            processed_path,
            "--fill-value=nan",
            "-o",
            filled_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(filled_path)


def test_mean_command(tmp_prepdata_type2_path, tmp_path):
    mean_path = tmp_path / "MeanProfile.h5"
    subprocess.run(
        [
            "heavyedge",
            "mean",
            "--wnum",
            "100",
            tmp_prepdata_type2_path,
            "-o",
            mean_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(mean_path)


def test_edge_command(tmp_prepdata_type2_path, tmp_path):
    area_scaled_path = tmp_path / "AreaScaledProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "scale",
            tmp_prepdata_type2_path,
            "--type=area",
            "-o",
            area_scaled_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(area_scaled_path)

    plateau_scaled_path = tmp_path / "PlateauScaledProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "scale",
            tmp_prepdata_type2_path,
            "--type=plateau",
            "-o",
            plateau_scaled_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(plateau_scaled_path)

    trimmed_path = tmp_path / "TrimmedProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "trim",
            tmp_prepdata_type2_path,
            "-o",
            trimmed_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(trimmed_path)

    padded_path = tmp_path / "PaddedProfiles.h5"
    subprocess.run(
        [
            "heavyedge",
            "pad",
            tmp_prepdata_type2_path,
            "-o",
            padded_path,
        ],
        capture_output=True,
        check=True,
    )
    assert os.path.exists(padded_path)


def test_filter_command(tmp_prepdata_type2_path, tmp_path):
    sorted_idx = [1, 2, 3]
    sorted_idx_path = tmp_path / "sorted.npy"
    sorted_profiles_path = tmp_path / "sorted.h5"
    np.save(sorted_idx_path, sorted_idx)
    subprocess.run(
        [
            "heavyedge",
            "filter",
            tmp_prepdata_type2_path,
            sorted_idx_path,
            "-o",
            sorted_profiles_path,
        ],
        capture_output=True,
        check=True,
    )

    reversed_idx = list(reversed(sorted_idx))
    reversed_idx_path = tmp_path / "reversed.npy"
    reversed_profiles_path = tmp_path / "reversed.h5"
    np.save(reversed_idx_path, reversed_idx)
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [
                "heavyedge",
                "filter",
                tmp_prepdata_type2_path,
                reversed_idx_path,
                "-o",
                reversed_profiles_path,
            ],
            capture_output=True,
            check=True,
        )
    subprocess.run(
        [
            "heavyedge",
            "filter",
            tmp_prepdata_type2_path,
            reversed_idx_path,
            "--unsorted",
            "-o",
            reversed_profiles_path,
        ],
        capture_output=True,
        check=True,
    )

    with ProfileData(sorted_profiles_path) as sorted_file:
        sorted_data = sorted_file[:]
    with ProfileData(reversed_profiles_path) as reversed_file:
        reversed_data = reversed_file[:]
    assert all(np.all(sd == rvd[::-1]) for sd, rvd in zip(sorted_data, reversed_data))
