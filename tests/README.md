# DTSGUI Baseline Test System

## What the baseline is

The `tests/baseline/` directory contains **golden fixture files** captured from
the unmodified DTSGUI data layer running under **CPython 2.7.14**. These files
are the permanent ground truth for validating that future code changes
(such as Python 3.13 migration) do not alter the
application's scientific behaviour.

## What is captured

For each test dataset (quashnet channel 1 & 2, santuit channel 1):

- Every public method on `Dataset` and `RawDataset` is called
- Every public method on `Channel` is called
- `Geodata` and `Subsets` methods are called
- Results are serialised in **strictly lossless formats**:
  - **numpy arrays** → `.npy` (binary, exact dtype preservation)
  - **pandas DataFrames** → `.csv` with `%.17g` float precision
  - **scalars/dicts/lists** → `.json`
  - **exceptions** → `.error.json` (exception class + message)

See `tests/BASELINE_MANIFEST.md` for the complete list of methods, arguments
used, and expected errors.

## How it is used

After migrating to Python 3.13, a `pytest`-based regression test suite
(`tests/test_regression.py`) will:

1. Load each `.npy` fixture with `np.load()`
2. Load each `.csv` fixture with `pd.read_csv()`
3. Load each `.json` fixture with `json.load()`
4. Re-run the same method call under the migrated Python 3.13 code
5. Assert outputs match within tolerance:
   - `np.testing.assert_allclose(actual, expected, rtol=1e-5)`
   - `pd.testing.assert_frame_equal(actual, expected, check_exact=False, rtol=1e-5)`
   - Direct equality for scalars/dicts, `pytest.approx` for floats
   - `pytest.raises(ExpectedException)` for `.error.json` fixtures

## File organisation

```
tests/
├── baseline/
│   ├── quashnet_channel1/
│   │   ├── data/           # Dataset method outputs
│   │   ├── data_raw/       # RawDataset method outputs
│   │   ├── geodata/        # Geodata method outputs
│   │   ├── subsets/        # Subsets method outputs
│   │   └── channel.*.json  # Channel method outputs
│   ├── quashnet_channel2/
│   │   └── (same structure)
│   └── santuit_channel1/
│       └── (same structure)
├── BASELINE_MANIFEST.md    # What was captured, how, and why
└── README.md               # This file
```
