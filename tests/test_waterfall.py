import os
import sys
import pytest
import numpy as np
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dts.data.io.therma_csv import ThermaCSVData
from dts.ui.plot.waterfall import GenericData

TEST_CSV_PATH = os.path.join(REPO_ROOT, "samples", "DTS_J1_ThermaCSV.csv")


@pytest.fixture
def csv_data():
    return ThermaCSVData.from_file(TEST_CSV_PATH)


def test_parse_csv_shape(csv_data):
    assert len(csv_data.times) == 38
    assert len(csv_data.depths) == 10264
    assert csv_data.temperatures.shape == (38, 10264)


def test_parse_csv_depths(csv_data):
    assert csv_data.depths[0] == 0.0
    assert csv_data.depths[-1] == 5131.5
    assert csv_data.depths[1] - csv_data.depths[0] == 0.5


def test_parse_csv_times(csv_data):
    assert csv_data.times[0].year == 2026
    assert csv_data.times[0].month == 5
    assert csv_data.times[0].day == 19
    assert csv_data.times[0].hour == 12
    assert csv_data.times[0].minute == 59

    assert csv_data.times[-1].year == 2026
    assert csv_data.times[-1].month == 5
    assert csv_data.times[-1].day == 22
    assert csv_data.times[-1].hour == 13
    assert csv_data.times[-1].minute == 18


def test_parse_csv_values(csv_data):
    assert abs(csv_data.temperatures[0, 0] - 25.997) < 1e-5
    assert abs(csv_data.temperatures[1, 0] - 27.844) < 1e-5


def test_thermacsvdata_auto_clip_depth(csv_data):
    min_d, max_d = csv_data.auto_clip_depth()
    assert min_d == 0.0
    assert max_d <= 5131.5


def test_thermacsvdata_manual_clip_depth(csv_data):
    clipped = csv_data.get_clipped(10.0, 50.0)
    assert clipped.depths[0] == 10.0
    assert clipped.depths[-1] == 50.0
    assert clipped.temperatures.shape == (38, len(clipped.depths))


def test_therma_csv_empty_file(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")
    with pytest.raises(ValueError) as excinfo:
        ThermaCSVData.from_file(str(empty_csv))
    assert "File is empty or missing headers" in str(excinfo.value)


class DummyNativeDataset:
    def __init__(self):
        self.times = [
            datetime(2026, 1, 1, 0, 0).timestamp(),
            datetime(2026, 1, 1, 1, 0).timestamp(),
            datetime(2026, 1, 1, 2, 0).timestamp(),
        ]
        self.depths = np.array([0.0, 1.0, 2.0, 3.0])
        self.temps = np.array(
            [
                [20.0, 21.0, 22.0, 23.0],
                [24.0, 25.0, 26.0, 27.0],
                [28.0, 29.0, 30.0, 31.0],
            ]
        )

    def get_times_list(self):
        return self.times

    def get_dist_array(self):
        return self.depths

    def get_array(self):
        return self.temps


class InvalidDummyDataset:
    def get_array(self):
        return np.array([1, 2])


def test_native_dataset_preprocessing():
    ds = DummyNativeDataset()
    gdata = GenericData(ds)
    assert len(gdata.times) == 3
    assert len(gdata.depths) == 4
    assert gdata.temps.shape == (3, 4)
    assert gdata.temps[1, 2] == 26.0


def test_generic_data_invalid_dataset():
    with pytest.raises(TypeError) as excinfo:
        GenericData(InvalidDummyDataset())
    assert "required methods" in str(excinfo.value)


def test_generic_data_invalid_csv_path(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("just\nsome\nrandom\ntext")
    with pytest.raises(ValueError) as excinfo:
        GenericData(str(bad_csv))
    assert "Invalid date format in Therma CSV" in str(
        excinfo.value
    ) or "Missing time data" in str(excinfo.value)


def test_generic_data_clipping_bounds():
    ds = DummyNativeDataset()
    gdata = GenericData(ds)

    clipped1 = gdata.get_clipped(min_depth=1.0, max_depth=2.0)
    assert len(clipped1.depths) == 2
    assert clipped1.temps.shape == (3, 2)

    t1 = datetime(2026, 1, 1, 1, 0)
    clipped2 = gdata.get_clipped(min_depth=0.0, max_depth=3.0, min_time=t1, max_time=t1)
    assert len(clipped2.times) == 1
    assert clipped2.temps.shape == (1, 4)
    assert clipped2.temps[0, 0] == 24.0


def test_generic_data_clipping_out_of_bounds():
    ds = DummyNativeDataset()
    gdata = GenericData(ds)

    clipped = gdata.get_clipped(min_depth=100.0, max_depth=200.0)
    assert len(clipped.depths) == 4
    assert clipped.temps.shape == (3, 4)


def test_generic_data_auto_clip_depth():
    ds = DummyNativeDataset()
    gdata = GenericData(ds)
    gdata.temps[0, 3] = -150.0

    min_d, max_d = gdata.auto_clip_depth()
    assert min_d == 0.0
    assert max_d == 2.0
