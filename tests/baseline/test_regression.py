import json
import os
import tempfile
import pytest
import numpy as np
import pandas as pd

import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dts.data import DataFile
from dts.data.io import import_data

TEST_DATA_DIR = os.path.join(REPO_ROOT, "test", "data")
BASELINE_DIR = os.path.join(REPO_ROOT, "tests", "baseline")

DATASETS = [
    (
        "quashnet_channel1",
        os.path.join(TEST_DATA_DIR, "quashnet", "channel1"),
        "sensornet",
        "channel1",
    ),
    (
        "quashnet_channel2",
        os.path.join(TEST_DATA_DIR, "quashnet", "channel2"),
        "sensornet",
        "channel2",
    ),
    (
        "santuit_channel1",
        os.path.join(TEST_DATA_DIR, "santuit", "Channel1"),
        "silixa",
        "channel1",
    ),
]

# cache datafile obj
_datafiles = {}


@pytest.fixture(scope="module")
def loaded_channels():
    channels = {}
    temp_files = []

    for stem, folder, file_type, channel_name in DATASETS:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".h5")
        os.close(tmp_fd)
        temp_files.append(tmp_path)

        datafile = DataFile(tmp_path, create=True)
        channel = import_data(datafile, channel_name, folder, file_type)

        channels[stem] = channel
        _datafiles[stem] = datafile

    yield channels

    for datafile in _datafiles.values():
        datafile.close()

    for tmp_path in temp_files:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def load_fixture(stem, category, method_name):
    # "data", "data_raw", "channel", "geodata", "subsets"
    if category == "channel":
        base_path = os.path.join(BASELINE_DIR, stem, method_name)
    elif category == "geodata" or category == "subsets":
        base_path = os.path.join(BASELINE_DIR, stem, category, method_name)
    else:
        base_path = os.path.join(BASELINE_DIR, stem, category, method_name)

    error_path = base_path + ".error.json"
    if os.path.exists(error_path):
        with open(error_path) as f:
            err_data = json.load(f)
        return {"error": err_data}

    if os.path.exists(base_path + ".npy"):
        return {"npy": np.load(base_path + ".npy")}

    if os.path.exists(base_path + ".csv"):
        return {"csv": pd.read_csv(base_path + ".csv", index_col=0)}

    if os.path.exists(base_path + ".json"):
        with open(base_path + ".json") as f:
            return {"json": json.load(f)}

    if category == "channel":
        base_path = os.path.join(BASELINE_DIR, stem, "channel." + method_name)
        error_path = base_path + ".error.json"
        if os.path.exists(error_path):
            with open(error_path) as f:
                err_data = json.load(f)
            return {"error": err_data}

        if os.path.exists(base_path + ".npy"):
            return {"npy": np.load(base_path + ".npy")}

        if os.path.exists(base_path + ".csv"):
            return {"csv": pd.read_csv(base_path + ".csv", index_col=0)}

        if os.path.exists(base_path + ".json"):
            with open(base_path + ".json") as f:
                return {"json": json.load(f)}

    pytest.skip(f"Fixture {base_path} not found")


def assert_matches_fixture(actual, fixture_data):
    if "error" in fixture_data:
        err_info = fixture_data["error"]
        pytest.fail(
            f"Expected exception {err_info['exception_class']} but none was raised. Value returned: {actual}"
        )

    if "npy" in fixture_data:
        expected = fixture_data["npy"]
        if hasattr(actual, "dtype") and actual.dtype.names:
            for name in actual.dtype.names:
                np.testing.assert_allclose(actual[name], expected[name], rtol=1e-5)
        else:
            np.testing.assert_allclose(actual, expected, rtol=1e-5)

    elif "csv" in fixture_data:
        expected = fixture_data["csv"]
        if isinstance(actual, pd.Series):
            actual = actual.to_frame()

        try:
            expected.index = pd.to_datetime(expected.index)
        except Exception:
            pass

        if not expected.columns.empty and isinstance(actual.columns[0], float):
            expected.columns = expected.columns.astype(float)

        pd.testing.assert_frame_equal(
            actual,
            expected,
            check_exact=False,
            rtol=1e-5,
            check_dtype=False,
            check_index_type=False,
            check_column_type=False,
        )

    elif "json" in fixture_data:
        expected = fixture_data["json"]
        if isinstance(actual, np.ndarray):
            actual = actual.tolist()
        elif isinstance(actual, pd.Series):
            actual = actual.tolist()
        elif isinstance(actual, tuple):
            actual = list(actual)
        elif type(actual).__name__ == "dict_keys":
            actual = list(actual)

        if isinstance(expected, dict) and expected.get("note") == "geodata not loaded":
            assert actual is False or actual is None
        elif isinstance(expected, float):
            assert actual == pytest.approx(expected, rel=1e-5)
        elif (
            isinstance(expected, list)
            and len(expected) > 0
            and isinstance(expected[0], float)
        ):
            assert np.allclose(actual, expected, rtol=1e-5)
        else:
            assert actual == expected


def execute_and_assert(obj, method_name, fixture_data, kwargs=None):
    kwargs = kwargs or {}
    try:
        method = getattr(obj, method_name)
        actual = method(**kwargs)
    except Exception as exc:
        if "error" in fixture_data:
            err_info = fixture_data["error"]
            assert type(exc).__name__ == err_info["exception_class"]
            return
        else:
            raise

    assert_matches_fixture(actual, fixture_data)


def pytest_generate_tests(metafunc):
    if "method_test_case" in metafunc.fixturenames:
        test_cases = []
        for stem, _, _, _ in DATASETS:
            # dataset methods
            methods_dataset = [
                "get_array",
                "get_times_list",
                "get_offset",
                "get_interval",
                "get_xmin",
                "get_tmin",
                "get_xrange",
                "get_trange",
                "is_subset",
                "get_dist_range",
                "get_dist_array",
                "get_temp_range",
                "get_data_frame",
                "get_title",
                "get_distance_interval",
            ]
            for method in methods_dataset:
                test_cases.append((stem, "data", method, None))
                test_cases.append((stem, "data_raw", method, None))

            test_cases.append((stem, "data", "get_bounds", None))
            test_cases.append((stem, "data_raw", "get_bounds", None))

            test_cases.append((stem, "data", "get_bounds", {"format": "timespace"}))
            test_cases.append((stem, "data_raw", "get_bounds", {"format": "timespace"}))

            # get_dist and get_time with keys
            if stem == "quashnet_channel1":
                dist_keys = [0, 497, 994]
                time_keys = [0, 132, 264]
            elif stem == "quashnet_channel2":
                dist_keys = [0, 497, 994]
                time_keys = [0, 132, 263]
            else:
                dist_keys = [0, 983, 1965]
                time_keys = [0, 94, 188]

            for key in dist_keys:
                test_cases.append((stem, "data", "get_dist", {"array_key": key}))
                test_cases.append((stem, "data_raw", "get_dist", {"array_key": key}))
                test_cases.append((stem, "channel", "get_dist", {"array_key": key}))

            for key in time_keys:
                test_cases.append((stem, "data", "get_time", {"array_key": key}))
                test_cases.append((stem, "data_raw", "get_time", {"array_key": key}))

            for key in time_keys[:2]:  # channel get_time only had 0 and mid
                test_cases.append((stem, "channel", "get_time", {"array_key": key}))

            # channel methods
            methods_channel = [
                "get_title",
                "get_key",
                "get_times_list",
                "get_offset",
                "get_interval",
                "get_dist_range",
                "get_time_range",
                "get_temp_range",
            ]
            for method in methods_channel:
                test_cases.append((stem, "channel", method, None))

            # geodata methods
            test_cases.append((stem, "geodata", "get_raw", None))
            test_cases.append((stem, "geodata", "get_interpolated", None))
            test_cases.append((stem, "geodata", "get_center", None))

            # subsets methods
            test_cases.append((stem, "subsets", "keys", None))

        ids = [
            f"{stem}-{cat}-{method}{'_' + str(list(kwargs.values())[0]) if kwargs else ''}"
            for stem, cat, method, kwargs in test_cases
        ]
        metafunc.parametrize("method_test_case", test_cases, ids=ids)


def test_regression(loaded_channels, method_test_case):
    stem, category, method_name, kwargs = method_test_case

    channel = loaded_channels[stem]
    if category == "data":
        obj = channel.data
    elif category == "data_raw":
        obj = channel.data_raw
    elif category == "channel":
        obj = channel
    elif category == "geodata":
        obj = channel.geodata
    elif category == "subsets":
        obj = channel.subsets
    else:
        pytest.fail(f"Unknown category {category}")

    out_name = method_name
    if kwargs:
        if method_name == "get_bounds":
            out_name = "get_bounds_timespace"
        else:
            out_name = f"{method_name}_{list(kwargs.values())[0]}"

    if category == "channel":
        pass
    elif category == "geodata":
        out_name = "geodata." + out_name
    elif category == "subsets":
        out_name = "subsets." + out_name

    fixture_data = load_fixture(stem, category, out_name)
    execute_and_assert(obj, method_name, fixture_data, kwargs)
