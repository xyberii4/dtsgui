import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dts.data.io.therma_csv import ThermaCSVData

TEST_CSV_PATH = os.path.join(REPO_ROOT, "samples", "DTS_J1_ThermaCSV.csv")

@pytest.fixture
def csv_data():
    return ThermaCSVData.from_file(TEST_CSV_PATH)

def test_parse_csv_shape(csv_data):
    # Expect 38 time steps, 10264 depth points
    assert len(csv_data.times) == 38
    assert len(csv_data.depths) == 10264
    assert csv_data.temperatures.shape == (38, 10264)

def test_parse_csv_depths(csv_data):
    assert csv_data.depths[0] == 0.0
    assert csv_data.depths[-1] == 5131.5
    # Check spacing
    assert csv_data.depths[1] - csv_data.depths[0] == 0.5

def test_parse_csv_times(csv_data):
    # '2026-05-19 12:59:27'
    assert csv_data.times[0].year == 2026
    assert csv_data.times[0].month == 5
    assert csv_data.times[0].day == 19
    assert csv_data.times[0].hour == 12
    assert csv_data.times[0].minute == 59
    
    # '2026-05-22 13:18:57'
    assert csv_data.times[-1].year == 2026
    assert csv_data.times[-1].month == 5
    assert csv_data.times[-1].day == 22
    assert csv_data.times[-1].hour == 13
    assert csv_data.times[-1].minute == 18

def test_parse_csv_values(csv_data):
    # Row 3, Col 1 -> Depth 0.0, Time 0 -> 25.997
    assert abs(csv_data.temperatures[0, 0] - 25.997) < 1e-5
    # Row 3, Col 2 -> Depth 0.0, Time 1 -> 27.844
    assert abs(csv_data.temperatures[1, 0] - 27.844) < 1e-5

def test_auto_clip_depth(csv_data):
    min_d, max_d = csv_data.auto_clip_depth()
    assert min_d == 0.0
    # The valid depths should end where the extreme noise/sentinels begin
    assert max_d <= 5131.5

def test_manual_clip_depth(csv_data):
    clipped = csv_data.get_clipped(10.0, 50.0)
    assert clipped.depths[0] == 10.0
    assert clipped.depths[-1] == 50.0
    assert clipped.temperatures.shape == (38, len(clipped.depths))
