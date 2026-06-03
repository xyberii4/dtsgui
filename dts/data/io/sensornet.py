import numpy as np
from time import strptime, mktime
import logging as log

from .base import Importer


class SensornetImporter(Importer):
    """Sensornet data import class

    Parameters
    ----------
    folder : str
        Directory containing Sensornet data files

    """

    type_map = ["dtd", "ddf"]
    time_format = "%Y/%m/%d %H:%M:%S"

    def _getline(self, filename, lineno):
        with open(filename, "r", encoding="latin1") as f:
            for i, line in enumerate(f):
                if i == lineno - 1:
                    return line
        return ""

    def get_interval(self):
        """Returns the spatial interval

        Returns
        -------
        float

        """

        interval = 1.0

        if self.file_type == "dtd":
            interval = float(self._getline(self.files[0], 13)[0:-1])

        elif self.file_type == "ddf":
            lengths = np.loadtxt(self.files[0], skiprows=26, dtype="f", usecols=(0,))

            intervals = lengths[1:] - lengths[0:-1]
            mean = intervals.mean()
            log.info(
                "Intervals: min {0}, max {1}, mean {2}".format(
                    intervals.min(), intervals.max(), mean
                )
            )
            interval = round(mean, 4)

        log.info("Interval - {0:.4f}".format(interval))

        return interval

    def load_ddf(self, filename):
        """Loads temperature and time data from a Sensornet DDF file

        Parameters
        ----------
        filename : str
            Data file name

        Returns
        -------
        numpy.ndarray, numpy.ndarray
            temperatures, time

        """

        d = self._getline(filename, 10)
        t = self._getline(filename, 11)
        ls = [i.split("\t")[1].rstrip() for i in [d, t]]
        time = self.__get_time(" ".join(ls))

        data = np.loadtxt(
            filename, skiprows=26, usecols=(0, 1), dtype="f", encoding="latin1"
        )

        # Get rid of data that is outside of normal range.
        temperatures = data[:, 1][data[:, 0] > 0]

        return temperatures, time

    def load_dtd(self, filename):
        """Loads temperature and time data from a Sensornet DDF file

        Parameters
        ----------
        filename : str
            Data file name

        Returns
        -------
        numpy.ndarray, numpy.ndarray
            temperatures, time

        """

        d = self._getline(filename, 8).rstrip()
        t = self._getline(filename, 9).rstrip()

        time = self.__get_time(d + " " + t)

        temperatures = np.loadtxt(filename, skiprows=13, dtype="f", encoding="latin1")
        return temperatures, time

    def load_file(self, filename):
        """Loads a Sensornet data file

        Parameters
        ----------
        filename : str
            Data file name

        Returns
        -------
        numpy.ndarray, numpy.ndarray
            temperatures, time

        """
        loaderMethod = getattr(self, "load_" + self.file_type)
        return loaderMethod(filename)

    def __get_time(self, timestring):
        date = strptime(timestring, self.time_format)
        return mktime(date)
