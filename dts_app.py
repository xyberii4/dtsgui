import wx
import dts
import sys
import traceback

from dts.ui.window import GraphFrame

"""
This file is the major entry-point into the DTS application that initializes the GUI after asking for user options 
(and with production error-catching routines in place). This is the file you would use if running the entire application
 from source, as such:
    ``python dts_app.py``
"""

if __name__ == "__main__":
    try:
        dts.DEBUG = False

        dts.logging.set_critical()
        app = dts.Application()

        init = dts.Initialize()

        app.data = init.data

        app.frame = GraphFrame(app)

        app.frame.Show()
        sys.exit(app.MainLoop())

    except Exception as err:
        err = str(err)
        xc = traceback.format_exception(*sys.exc_info())
        err = "DTS GUI debug message:\n" + "".join(xc)
        print(err, file=sys.stderr)
        sys.exit(1)
