# DTSGUI

DTSGUI is a public-domain software tool to import, manage, parse/cull, georeference, analyze and visualize fiber-optic distributed temperature sensor (FO-DTS) data. Visualization can efficiently be accomplished in the form of “heat maps” of temperature (as color) versus distance and time, and in map view plots of georeferenced data on land-surface orthoimagery. The code is written in object-oriented Python to facilitate future extension. Data analysis is implemented using tools from the Python libraries NumPy and SciPy, and the graphical user interface (GUI) is implemented using the Python library wx. DTSGUI imports FO-DTS data in two common formats along with spatial coordinates of the FO-DTS cables, plots data and summary statistics (e.g., standard deviation, mean, minimum, maximum) in space and time, and overlays data spatially on maps retrieved from Google Maps using the Google Maps API.

NOTE: the automated map feature using Google Maps for georeferenced data is not functional. A fix is in progress as of March 2026.

## Waterfall Visualization

DTSGUI features an interactive waterfall viewer for visualizing temperature as a color gradient against cable distance and time.

- **Interactive Profiles:** Points on the waterfall plot to open 1D time or depth profiles in an external window. Subsequent clicks append to the existing plot.
- **Custom Boundaries:** Set temperature limits, temporal ranges, and depth intervals.
- **Export:** Save high-resolution figures of any visualization directly to disk.

**Data Requirements:**
The waterfall component is compatible with standard XML and DTD formats loaded into the application workspace. It additionally supports Therma CSV formats structured with timestamps along the horizontal axis and depth intervals along the vertical axis.

## Tutorial

See [TUTORIAL.md](docs/TUTORIAL.md) for a quick start tutorial.

## Google Maps API key

Email [aetucker@usgs.gov](mailto:aetucker@usgs.gov) or [mbriggs@usgs.gov](malto:mbriggs@usgs.gov) to request an API key for the Google Maps feature.

## Local Development

Dependency management has been migrated to [Pixi](https://pixi.sh).

To install dependencies and run the application:

```bash
pixi install
pixi run run
```
