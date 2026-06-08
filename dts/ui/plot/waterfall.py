import wx
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime

from dts.ui.plot import PlotPanel


class GenericData:
    def __init__(self, data_source):
        if isinstance(data_source, str):
            from dts.data.io.therma_csv import ThermaCSVData

            try:
                self.raw_data = ThermaCSVData.from_file(data_source)
            except Exception as e:
                raise ValueError(f"Failed to load CSV: {str(e)}")
            self.times = self.raw_data.times  # list of datetimes
            self.depths = self.raw_data.depths  # np.ndarray
            # temps: (n_times, n_depths)
            self.temps = self.raw_data.temperatures
        else:
            if (
                not hasattr(data_source, "get_times_list")
                or not hasattr(data_source, "get_dist_array")
                or not hasattr(data_source, "get_array")
            ):
                raise TypeError(
                    "Data source must be a valid Dataset object with required methods (get_times_list, get_dist_array, get_array)."
                )

            self.raw_data = data_source
            times_list = self.raw_data.get_times_list()
            self.times = [datetime.fromtimestamp(t) for t in times_list]
            self.depths = self.raw_data.get_dist_array()
            # temps: (n_times, n_depths)
            self.temps = self.raw_data.get_array()[:]
            if self.temps.shape[0] != len(self.times):
                self.temps = self.temps.T

    def get_clipped(self, min_depth, max_depth, min_time=None, max_time=None):
        mask_depth = (self.depths >= min_depth) & (self.depths <= max_depth)
        if not np.any(mask_depth):
            # fallback if empty
            mask_depth = np.ones(len(self.depths), dtype=bool)

        new_depths = self.depths[mask_depth]

        times_arr = np.array(self.times)
        if min_time and max_time:
            mask_time = (times_arr >= min_time) & (times_arr <= max_time)
            if not np.any(mask_time):
                mask_time = np.ones(len(times_arr), dtype=bool)
        else:
            mask_time = np.ones(len(times_arr), dtype=bool)

        new_times = times_arr[mask_time].tolist()

        # self.temps is (n_times, n_depths)
        # apply mask_time on axis 0, mask_depth on axis 1
        new_temps = self.temps[mask_time][:, mask_depth]

        res = type("GenericDataClipped", (object,), {})()
        res.times = new_times
        res.depths = new_depths
        res.temps = new_temps
        return res

    def auto_clip_depth(self):
        last_valid_idx = 0
        for j in range(len(self.depths)):
            depth_temps = self.temps[:, j]
            if np.any(depth_temps < -100) or np.any(depth_temps > 100):
                break
            last_valid_idx = j

        return float(self.depths[0]), float(self.depths[last_valid_idx])


class ProfileFrame(wx.Frame):
    def __init__(self, parent_panel, title, is_time_profile=True, depth_on_x=True):
        super().__init__(parent_panel.GetTopLevelParent(), title=title, size=(800, 500))
        self.parent_panel = parent_panel
        self.SetMinSize((800, 500))
        self.is_time_profile = is_time_profile
        self.depth_on_x = depth_on_x

        self.plot_panel = PlotPanel(self, dpi=100)
        self.plot_panel.figure.set_size_inches(8, 5)
        self.ax = self.plot_panel.figure.add_subplot(111)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.plot_panel, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(self.sizer)

        self.lines = []
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def add_profile_line(self, x_data, y_data, label):
        (line,) = self.ax.plot(
            x_data, y_data, marker="o", linewidth=1.5, markersize=4, label=label
        )
        self.lines.append(line)

        self.ax.grid(True, linestyle="--", alpha=0.6)
        if self.is_time_profile:
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Temperature [°C]")
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
            self.plot_panel.figure.autofmt_xdate()
        else:
            if self.depth_on_x:
                self.ax.set_xlabel("Depth [m]")
                self.ax.set_ylabel("Temperature [°C]")
            else:
                self.ax.set_xlabel("Temperature [°C]")
                self.ax.set_ylabel("Depth [m]")
                if len(self.lines) == 1:
                    self.ax.invert_yaxis()

        self.ax.legend()
        self.plot_panel.figure.tight_layout()

        if self.is_time_profile:
            self.plot_panel.figure.subplots_adjust(bottom=0.25)
        else:
            self.plot_panel.figure.subplots_adjust(bottom=0.15)

        self.plot_panel.canvas.draw()
        self.Layout()

    def on_close(self, event):
        self.parent_panel.profile_frame = None
        self.Destroy()


class WaterfallViewer(wx.Panel):
    def __init__(self, parent, data_source, id=wx.ID_ANY, **kwargs):
        super().__init__(parent, id=id, **kwargs)
        self.generic_data = GenericData(data_source)
        self.current_data = self.generic_data

        self.profile_frame = None
        self.last_profile_is_time = None
        self.last_depth_on_x = None

        self._init_ui()
        self.render_plot()

    def _init_ui(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_toolbar = wx.Panel(self)
        control_sizer = wx.BoxSizer(wx.VERTICAL)

        # profile type and limits
        row1 = wx.BoxSizer(wx.HORIZONTAL)

        self.rb_profile_type = wx.RadioBox(
            self.control_toolbar,
            label="On Click Profile Type",
            choices=["Time Profile", "Depth Profile"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.rb_profile_type.Bind(wx.EVT_RADIOBOX, self.on_profile_type_changed)
        row1.Add(self.rb_profile_type, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.rb_depth_orient = wx.RadioBox(
            self.control_toolbar,
            label="Depth Orientation",
            choices=["Depth on X", "Depth on Y"],
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.rb_depth_orient.Enable(False)
        row1.Add(self.rb_depth_orient, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.btn_auto_clip = wx.Button(
            self.control_toolbar, label="Auto-detect Depth Range"
        )
        self.btn_auto_clip.Bind(wx.EVT_BUTTON, self.on_auto_clip)
        row1.Add(self.btn_auto_clip, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.btn_refresh = wx.Button(self.control_toolbar, label="Refresh Plot")
        self.btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
        row1.Add(self.btn_refresh, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        control_sizer.Add(row1, 0, wx.EXPAND)

        # limits inputs
        row2 = wx.BoxSizer(wx.HORIZONTAL)

        # depth limits
        row2.Add(
            wx.StaticText(self.control_toolbar, label="Min Depth:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_min_depth = wx.SpinCtrlDouble(
            self.control_toolbar,
            value=str(self.generic_data.depths[0]),
            min=-10000,
            max=10000,
            inc=0.5,
        )
        row2.Add(self.spin_min_depth, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        row2.Add(
            wx.StaticText(self.control_toolbar, label="Max Depth:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_max_depth = wx.SpinCtrlDouble(
            self.control_toolbar,
            value=str(self.generic_data.depths[-1]),
            min=-10000,
            max=10000,
            inc=0.5,
        )
        row2.Add(self.spin_max_depth, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # time limits
        t_start = self.generic_data.times[0].strftime("%Y-%m-%d %H:%M")
        t_end = self.generic_data.times[-1].strftime("%Y-%m-%d %H:%M")
        row2.Add(
            wx.StaticText(self.control_toolbar, label="Start Time (YYYY-MM-DD HH:MM):"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.txt_min_time = wx.TextCtrl(
            self.control_toolbar, value=t_start, size=(120, -1)
        )
        row2.Add(self.txt_min_time, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        row2.Add(
            wx.StaticText(self.control_toolbar, label="End Time:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.txt_max_time = wx.TextCtrl(
            self.control_toolbar, value=t_end, size=(120, -1)
        )
        row2.Add(self.txt_max_time, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # temp limits
        self.chk_temp_limits = wx.CheckBox(
            self.control_toolbar, label="Custom Temp Limits"
        )
        row2.Add(self.chk_temp_limits, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        row2.Add(
            wx.StaticText(self.control_toolbar, label="Min T:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_min_temp = wx.SpinCtrlDouble(
            self.control_toolbar, value="20", min=-100, max=500, inc=0.5
        )
        row2.Add(self.spin_min_temp, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        row2.Add(
            wx.StaticText(self.control_toolbar, label="Max T:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_max_temp = wx.SpinCtrlDouble(
            self.control_toolbar, value="30", min=-100, max=500, inc=0.5
        )
        row2.Add(self.spin_max_temp, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        control_sizer.Add(row2, 0, wx.EXPAND)

        self.control_toolbar.SetSizer(control_sizer)
        self.sizer.Add(self.control_toolbar, 0, wx.EXPAND | wx.ALL, 5)

        self.plot_panel = PlotPanel(self, dpi=None)
        self.sizer.Add(self.plot_panel, 1, wx.EXPAND | wx.ALL, 0)

        self.plot_panel.figure.canvas.mpl_connect(
            "button_press_event", self.on_plot_click
        )

        self.SetSizer(self.sizer)

    def on_profile_type_changed(self, event):
        is_depth = self.rb_profile_type.GetSelection() == 1
        self.rb_depth_orient.Enable(is_depth)

    def on_auto_clip(self, event):
        min_d, max_d = self.generic_data.auto_clip_depth()
        self.spin_min_depth.SetValue(min_d)
        self.spin_max_depth.SetValue(max_d)
        self.apply_clip()

    def on_refresh(self, event):
        self.apply_clip()

    def apply_clip(self):
        min_d = self.spin_min_depth.GetValue()
        max_d = self.spin_max_depth.GetValue()

        try:
            min_t = datetime.strptime(
                self.txt_min_time.GetValue().strip(), "%Y-%m-%d %H:%M"
            )
        except ValueError:
            min_t = None

        try:
            max_t = datetime.strptime(
                self.txt_max_time.GetValue().strip(), "%Y-%m-%d %H:%M"
            )
        except ValueError:
            max_t = None

        if min_d < max_d:
            self.current_data = self.generic_data.get_clipped(
                min_d, max_d, min_t, max_t
            )
            self.render_plot()

    def render_plot(self):
        fig = self.plot_panel.figure
        fig.clear()

        ax = fig.add_subplot(111)

        times = mdates.date2num(self.current_data.times)
        depths = self.current_data.depths

        color_args = {}
        if self.chk_temp_limits.GetValue():
            color_args["vmin"] = self.spin_min_temp.GetValue()
            color_args["vmax"] = self.spin_max_temp.GetValue()

        mesh = ax.pcolormesh(
            times,
            depths,
            self.current_data.temps.T,
            cmap="jet",
            shading="auto",
            **color_args,
        )

        ax.set_ylabel("Depth [m]")
        ax.set_xlabel("Time")
        ax.invert_yaxis()

        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        fig.autofmt_xdate()
        ax.set_title("DTS Waterfall Plot — Click to open Profile")

        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label("Temperature [°C]", rotation=270, labelpad=15)

        self.plot_panel.canvas.draw()

    def on_plot_click(self, event):
        if event.inaxes is None:
            return

        is_time_profile = self.rb_profile_type.GetSelection() == 0
        depth_on_x = self.rb_depth_orient.GetSelection() == 0

        if self.profile_frame is not None:
            if self.last_profile_is_time != is_time_profile or (
                not is_time_profile and self.last_depth_on_x != depth_on_x
            ):
                self.profile_frame.Close()
                self.profile_frame = None

        self.last_profile_is_time = is_time_profile
        self.last_depth_on_x = depth_on_x

        if is_time_profile:
            clicked_depth = event.ydata
            closest_idx = (np.abs(self.current_data.depths - clicked_depth)).argmin()
            actual_depth = self.current_data.depths[closest_idx]

            temp_profile = self.current_data.temps[:, closest_idx]

            if self.profile_frame is None:
                self.profile_frame = ProfileFrame(
                    self, "Time Profile", is_time_profile=True
                )
                self.profile_frame.Show()

            x_data = self.current_data.times
            label = f"Depth: {actual_depth:.2f}m"
            self.profile_frame.add_profile_line(x_data, temp_profile, label)

        else:
            clicked_time = mdates.num2date(event.xdata).replace(tzinfo=None)
            times_arr = np.array(self.current_data.times)

            time_diffs = np.abs(times_arr - clicked_time)
            closest_idx = time_diffs.argmin()
            actual_time = self.current_data.times[closest_idx]

            temp_profile = self.current_data.temps[closest_idx, :]

            if self.profile_frame is None:
                self.profile_frame = ProfileFrame(
                    self, "Depth Profile", is_time_profile=False, depth_on_x=depth_on_x
                )
                self.profile_frame.Show()

            label = f"Time: {actual_time.strftime('%m/%d %H:%M')}"
            if depth_on_x:
                self.profile_frame.add_profile_line(
                    self.current_data.depths, temp_profile, label
                )
            else:
                self.profile_frame.add_profile_line(
                    temp_profile, self.current_data.depths, label
                )

    def save_image(self):
        if hasattr(self.plot_panel, "save_image"):
            self.plot_panel.save_image()
