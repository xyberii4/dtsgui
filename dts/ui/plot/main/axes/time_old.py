from dts.ui.plot.main.axes import AxesBase, minmax_opts
from dts.ui.colors import GRAY
import matplotlib


class TimePlot(AxesBase):
    name = "TimePlot"

    def __init__(self, *args, **kwargs):
        """Axis for the **Time Range** subplot of :ref:`main-viewer`."""

        AxesBase.__init__(self, *args, **kwargs)
        self.set_xlabel("Temperature (\u00b0C)")
        self.xaxis.set_label_position("top")
        locator = matplotlib.ticker.MaxNLocator(nbins=5, prune="both")
        self.xaxis.set_major_locator(locator)

        for tick in self.yaxis.get_major_ticks():
            tick.label1On = False

        temps = self.figure.parent.array[:, self.figure.parent.x_loc]
        time = self.figure.parent.data.get_times_list()
        t = range(len(temps))

        self.series = dict()

        plot = lambda y, color: self.plot(self.profiles["time"][y], t, color=color)
        min = self.profiles["time"]["min"]
        max = self.profiles["time"]["max"]
        from dts.ui.plot.etc import fill_between_vertical

        self.series["minmax"] = fill_between_vertical(self, min, max, t, **minmax_opts)

        (self.series["mean"],) = plot("mean", "red")

        (self.series["std"],) = plot("std", GRAY)

        (self.series["temp"],) = self.plot(temps, t, color="blue")

        ax = self.twiny()
        ax.plot(self.profiles["time"]["std"], t, color=GRAY)

        locator = matplotlib.ticker.NullLocator()
        ax.set_xlabel("Std dev", color=GRAY)
        locator = matplotlib.ticker.MaxNLocator(nbins=5, prune="lower")
        ax.xaxis.set_major_locator(locator)

        ax.xaxis.set_label_position("bottom")

        for tick in self.xaxis.get_major_ticks():
            tick.label2On = True
            tick.label1On = False

        for tick in ax.xaxis.get_major_ticks():
            tick.label2On = False
            tick.label1On = True

        for tl in ax.get_xticklabels():
            tl.set_color(GRAY)

        ax.set_visible(self.figure.parent.c_flags["std"])
        self._std_ax = ax

        for i, val in self.figure.parent.c_flags.items():
            self.series[i].set_visible(val)

    def set_visible(self, visible=True):
        AxesBase.set_visible(self, visible, orientation="columns", index=-1)
