# Baseline Manifest

This document records every golden fixture file captured from the DTSGUI
data layer under the original CPython 2.7.14 interpreter.

## Baseline Integrity Notes

- **Captured using CPython 2.7.14** (Anaconda, Inc.)
- **No transpiler or import hooks used** — only `sys.modules` pre-population
  to bypass `dts/__init__.py` (which imports `wx` and `matplotlib`)
- **Arrays stored as `.npy`** — lossless binary via `np.save()`; preserves
  exact float32/float64 dtype and shape
- **DataFrames stored as `.csv` with `%.17g` precision** — 17 significant
  figures, sufficient for exact float64 round-trip
- **Exceptions recorded as `.error.json`** — these are part of the baseline
  contract; a future regression test must assert that the same exception is
  still raised

## Test Data Files

| Path                           | Format          | Files |     Size | Notes                                              |
| ------------------------------ | --------------- | ----: | -------: | -------------------------------------------------- |
| `test/data/quashnet/channel1/` | Sensornet DTD   |   265 |  1.58 MB | CR-only line endings, latin-1 encoding (° symbol)  |
| `test/data/quashnet/channel2/` | Sensornet DTD   |   264 |  1.57 MB | CR-only line endings, latin-1 encoding             |
| `test/data/santuit/Channel1/`  | Silixa XML      |   189 | 27.55 MB | UTF-8 encoded XML                                  |
| `test/data/quashnet/*.txt`     | UTM coordinates |     2 |    <1 KB | Cable survey data (not imported by capture script) |

## Captured Methods

### Dataset (and RawDataset) methods

All methods below were called on both `channel.data` (Dataset) and
`channel.data_raw` (RawDataset) for each of the three test datasets.

| Method                           | Arguments            | Output File(s)                                                   | Status            |
| -------------------------------- | -------------------- | ---------------------------------------------------------------- | ----------------- |
| `get_array()`                    | none                 | `get_array.npy`, `get_array.meta.json`                           | OK                |
| `get_times_list()`               | none                 | `get_times_list.npy`, `get_times_list.meta.json`                 | OK                |
| `get_offset()`                   | none                 | `get_offset.json`                                                | OK                |
| `get_interval()`                 | none                 | `get_interval.json`                                              | OK                |
| `get_xmin()`                     | none                 | `get_xmin.json`                                                  | OK                |
| `get_tmin()`                     | none                 | `get_tmin.json`                                                  | OK                |
| `get_xrange()`                   | none                 | `get_xrange.json`                                                | OK                |
| `get_trange()`                   | none                 | `get_trange.json`                                                | OK                |
| `is_subset()`                    | none                 | `is_subset.json`                                                 | OK                |
| `get_bounds()`                   | none (format="xy")   | `get_bounds.json`                                                | OK                |
| `get_bounds(format="timespace")` | `format="timespace"` | `get_bounds_timespace.json`                                      | OK                |
| `get_dist_range()`               | none                 | `get_dist_range.error.json`                                      | ERROR (see below) |
| `get_dist_array()`               | none                 | `get_dist_array.npy`, `get_dist_array.meta.json`                 | OK                |
| `get_temp_range()`               | none                 | `get_temp_range.json`                                            | OK                |
| `get_data_frame()`               | none                 | `get_data_frame.csv`, `get_data_frame.meta.json`                 | OK                |
| `get_title()`                    | none                 | `get_title.json`                                                 | OK                |
| `get_distance_interval()`        | none                 | `get_distance_interval.json`                                     | OK                |
| `get_dist(array_key)`            | 0, mid, last         | `get_dist_0.json`, `get_dist_{mid}.json`, `get_dist_{last}.json` | OK                |
| `get_time(array_key)`            | 0, mid, last         | `get_time_0.json`, `get_time_{mid}.json`, `get_time_{last}.json` | OK                |

**Representative argument values used for `get_dist` and `get_time`:**

| Dataset           | Shape       | `get_dist` keys | `get_time` keys |
| ----------------- | ----------- | --------------- | --------------- |
| quashnet_channel1 | (265, 995)  | 0, 497, 994     | 0, 132, 264     |
| quashnet_channel2 | (264, 995)  | 0, 497, 994     | 0, 132, 263     |
| santuit_channel1  | (189, 1966) | 0, 983, 1965    | 0, 94, 188      |

### Channel methods

| Method                | Arguments    | Output File(s)                                                   | Status |
| --------------------- | ------------ | ---------------------------------------------------------------- | ------ |
| `get_title()`         | none         | `channel.get_title.json`                                         | OK     |
| `get_key()`           | none         | `channel.get_key.json`                                           | OK     |
| `get_times_list()`    | none         | `channel.get_times_list.npy`, `channel.get_times_list.meta.json` | OK     |
| `get_offset()`        | none         | `channel.get_offset.json`                                        | OK     |
| `get_interval()`      | none         | `channel.get_interval.json`                                      | OK     |
| `get_dist_range()`    | none         | `channel.get_dist_range.error.json`                              | ERROR  |
| `get_time_range()`    | none         | `channel.get_time_range.json`                                    | OK     |
| `get_temp_range()`    | none         | `channel.get_temp_range.json`                                    | OK     |
| `get_dist(array_key)` | 0, mid, last | `channel.get_dist_{key}.json`                                    | OK     |
| `get_time(array_key)` | 0, mid       | `channel.get_time_{key}.json`                                    | OK     |

### Geodata methods

| Method               | Arguments | Output File(s)                  | Status          |
| -------------------- | --------- | ------------------------------- | --------------- |
| `get_raw()`          | none      | `geodata.get_raw.json`          | OK (not loaded) |
| `get_interpolated()` | none      | `geodata.get_interpolated.json` | OK (not loaded) |
| `get_center()`       | none      | `geodata.get_center.error.json` | ERROR           |

### Subsets methods

| Method           | Arguments | Output File(s)      | Status |
| ---------------- | --------- | ------------------- | ------ |
| `Subsets.keys()` | none      | `subsets.keys.json` | OK     |

## Excluded — GUI Dependency

The following modules and methods were **excluded** from baseline capture
because they require `wx` or `matplotlib` at the module level:

| Module                        | Reason                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `dts/__init__.py`             | Imports `matplotlib` (line 1) and `wx` (line 5) at module level. Defines `Application(wx.App)` — a GUI class. |
| `dts/ui/*`                    | All UI modules import `wx` and `matplotlib` — purely GUI code.                                                |
| `Channel.merge_channels()`    | No-op (pass), not meaningful to capture.                                                                      |
| `Channel.revert_to_raw()`     | Mutates state destructively, not safe to call during capture.                                                 |
| `Channel.trim_raw()`          | Mutates state destructively, not safe to call during capture.                                                 |
| `DataFile.import_channel()`   | Uses `import io` (relative) which triggers the entire io subpackage. Tested indirectly via `import_data()`.   |
| `DataFile.combine_channels()` | Raises `NotImplementedError` by design.                                                                       |
| `Geodata.set_coords()`        | Mutator, not a read-only query.                                                                               |
| `Geodata.interpolate()`       | Internal method; tested indirectly via `get_interpolated()`.                                                  |
| `Subset.*` methods            | No subsets exist in the test data (empty dict).                                                               |

## Expected Errors

All 12 errors are pre-existing bugs in the original Python 2.7 source code.
They are **not** caused by the capture script.

### `get_dist_range` — `AttributeError: 'Dataset' object has no attribute 'data'` (9 occurrences)

`Dataset.get_dist_range()` at line 98 of `dataset.py` references `self.data.shape[1]`,
but the `Dataset` class stores its HDF5 dataset as `self.array`, not `self.data`.
Affects `Dataset`, `RawDataset`, and `Channel.get_dist_range()`.

| Method                                      | Error File                                             |
| ------------------------------------------- | ------------------------------------------------------ |
| `quashnet_channel1.data.get_dist_range`     | `quashnet_channel1/data/get_dist_range.error.json`     |
| `quashnet_channel1.data_raw.get_dist_range` | `quashnet_channel1/data_raw/get_dist_range.error.json` |
| `quashnet_channel1.channel.get_dist_range`  | `quashnet_channel1/channel.get_dist_range.error.json`  |
| `quashnet_channel2.data.get_dist_range`     | `quashnet_channel2/data/get_dist_range.error.json`     |
| `quashnet_channel2.data_raw.get_dist_range` | `quashnet_channel2/data_raw/get_dist_range.error.json` |
| `quashnet_channel2.channel.get_dist_range`  | `quashnet_channel2/channel.get_dist_range.error.json`  |
| `santuit_channel1.data.get_dist_range`      | `santuit_channel1/data/get_dist_range.error.json`      |
| `santuit_channel1.data_raw.get_dist_range`  | `santuit_channel1/data_raw/get_dist_range.error.json`  |
| `santuit_channel1.channel.get_dist_range`   | `santuit_channel1/channel.get_dist_range.error.json`   |

### `geodata.get_center` — `TypeError: 'bool' object has no attribute '__getitem__'` (3 occurrences)

`Geodata.get_center()` at line 27 of `geodata.py` tries to access
`self.raw['north']`, but when no geodata has been loaded, `self.raw` is
set to `False`. The method does not guard against the unloaded state.

| Method                                 | Error File                                                |
| -------------------------------------- | --------------------------------------------------------- |
| `quashnet_channel1.geodata.get_center` | `quashnet_channel1/geodata/geodata.get_center.error.json` |
| `quashnet_channel2.geodata.get_center` | `quashnet_channel2/geodata/geodata.get_center.error.json` |
| `santuit_channel1.geodata.get_center`  | `santuit_channel1/geodata/geodata.get_center.error.json`  |

## Summary

| Status    |   Count |
| --------- | ------: |
| OK        |     177 |
| ERROR     |      12 |
| **Total** | **189** |

**Baseline files written: 216 files** across `tests/baseline/`.
