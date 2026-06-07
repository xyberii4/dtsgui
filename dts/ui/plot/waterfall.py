import wx
import matplotlib.dates as mdates

from dts.ui.plot import PlotPanel
from dts.data.io.therma_csv import ThermaCSVData


class WaterfallViewer(wx.Panel):
    def __init__(self, parent, csv_path, id=wx.ID_ANY, **kwargs):
        super().__init__(parent, id=id, **kwargs)
        self.csv_path = csv_path
        self.csv_data = ThermaCSVData.from_file(csv_path)
        self.current_data = self.csv_data

        self._init_ui()
        self.render_plot()

    def _init_ui(self):
        # main layout
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # control toolbar
        self.control_toolbar = wx.Panel(self)
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # auto-detect btn
        self.btn_auto_clip = wx.Button(
            self.control_toolbar, label="Auto-detect Depth Range"
        )
        self.btn_auto_clip.Bind(wx.EVT_BUTTON, self.on_auto_clip)
        control_sizer.Add(self.btn_auto_clip, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        control_sizer.Add(
            wx.StaticText(self.control_toolbar, label="Min Depth (m):"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_min = wx.SpinCtrlDouble(
            self.control_toolbar,
            value=str(self.csv_data.depths[0]),
            min=-10000,
            max=10000,
            inc=0.5,
        )
        self.spin_min.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_manual_clip)
        control_sizer.Add(self.spin_min, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        control_sizer.Add(
            wx.StaticText(self.control_toolbar, label="Max Depth (m):"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        self.spin_max = wx.SpinCtrlDouble(
            self.control_toolbar,
            value=str(self.csv_data.depths[-1]),
            min=-10000,
            max=10000,
            inc=0.5,
        )
        self.spin_max.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_manual_clip)
        control_sizer.Add(self.spin_max, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        self.control_toolbar.SetSizer(control_sizer)
        self.sizer.Add(self.control_toolbar, 0, wx.EXPAND | wx.ALL, 5)

        # plot panels
        self.plot_panel = PlotPanel(self, dpi=None)
        self.sizer.Add(self.plot_panel, 1, wx.EXPAND | wx.ALL, 0)

        self.SetSizer(self.sizer)

    def on_auto_clip(self, event):
        min_d, max_d = self.csv_data.auto_clip_depth()
        self.spin_min.SetValue(min_d)
        self.spin_max.SetValue(max_d)
        self._apply_clip(min_d, max_d)

    def on_manual_clip(self, event):
        min_d = self.spin_min.GetValue()
        max_d = self.spin_max.GetValue()
        if min_d < max_d:
            self._apply_clip(min_d, max_d)

    def _apply_clip(self, min_d, max_d):
        self.current_data = self.csv_data.get_clipped(min_d, max_d)
        self.render_plot()

    def render_plot(self):
        fig = self.plot_panel.figure
        fig.clear()

        ax = fig.add_subplot(111)

        times = mdates.date2num(self.current_data.times)
        depths = self.current_data.depths

        # transpose temperatures (depths, times)
        mesh = ax.pcolormesh(
            times,
            depths,
            self.current_data.temperatures.T,
            cmap="viridis",
            shading="auto",
        )

        ax.set_ylabel("Depth [m]")
        ax.set_xlabel("Time")
        ax.invert_yaxis()  # depth is down

        ax.xaxis_date()
        fig.autofmt_xdate()

        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label("Temperature [°C]")

        self.plot_panel.canvas.draw()
