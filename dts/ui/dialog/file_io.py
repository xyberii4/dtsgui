"""Module containing shortcuts for common file and directory choice operations."""

import wx
import os


def choose_dir(title):
    dlg = wx.DirDialog(None, title, style=wx.DD_DEFAULT_STYLE)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
    else:
        path = False
    dlg.Destroy()
    return path


def choose_file(title, wildcard="All files (*.*)|*.*"):
    dlg = wx.FileDialog(
        None,
        message=title,
        defaultDir=os.getcwd(),
        defaultFile="",
        wildcard=wildcard,
        style=wx.FD_OPEN | wx.FD_CHANGE_DIR,
    )
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
    else:
        path = False
    dlg.Destroy()
    return path


def save_file(title, wildcard="All files (*.*)|*.*"):
    dlg = wx.FileDialog(
        None,
        message=title,
        defaultDir=os.getcwd(),
        defaultFile="",
        wildcard=wildcard,
        style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT,
    )
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
    else:
        path = False
    dlg.Destroy()
    return path


def open_csv_file(title="Choose a CSV file"):
    wildcard = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
    return choose_file(title, wildcard=wildcard)
