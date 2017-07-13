# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Wrappers around standard library functions used in vimiv."""

import gzip
import os
import re

from gi.repository import Gtk
from vimiv.exceptions import StringConversionError


def listdir_wrapper(path, show_hidden=False):
    """Re-implementation of os.listdir which mustn't show hidden files.

    Args:
        path: Path of the directory in which os.listdir is called.
        show_hidden: If true, show hidden files. Else do not.
    Return:
        Sorted list of files in path.
    """
    all_files = sorted(os.listdir(os.path.expanduser(path)))
    if show_hidden:
        return all_files
    return [fil for fil in all_files if not fil.startswith(".")]


def read_file(filename):
    """Read the content of a file into a list or create file.

    Args:
        filename: The name of the file to be read.
    Return:
        Content of filename in a list.
    """
    content = []
    try:
        with open(filename, "r") as f:
            for line in f:
                content.append(line.rstrip("\n"))
    except FileNotFoundError:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write("")
    return content


def sizeof_fmt(num):
    """Print size of a byte number in human-readable format.

    Args:
        num: Filesize in bytes.

    Return:
        Filesize in human-readable format.
    """
    for unit in ["B", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            if abs(num) < 100:
                return "%3.1f%s" % (num, unit)
            return "%3.0f%s" % (num, unit)
        num /= 1024.0
    return "%.1f%s" % (num, "Y")


def error_message(message, running_tests=False):
    """Show a GTK Error Pop Up with message.

    Args:
        message: The message to display.
        running_tests: If True running from testsuite. Do not show popup.
    """
    # Always print the error message first
    print("\033[91mError:\033[0m", message)
    # Then display a Gtk Popup
    popup = Gtk.Dialog(title="vimiv - Error", transient_for=Gtk.Window())
    popup.set_default_size(600, 1)
    popup.add_button("Close", Gtk.ResponseType.CLOSE)
    message_label = Gtk.Label()
    # Set up label so it actually follows the default width of 600
    message_label.set_hexpand(True)
    message_label.set_line_wrap(True)
    message_label.set_size_request(600, 1)
    message_label.set_text(message)
    box = popup.get_child()
    box.set_border_width(12)
    grid = Gtk.Grid()
    grid.set_column_spacing(12)
    box.pack_start(grid, False, False, 0)
    icon_size = Gtk.IconSize(5)
    error_icon = Gtk.Image.new_from_icon_name("dialog-error", icon_size)
    grid.attach(error_icon, 0, 0, 1, 1)
    grid.attach(message_label, 1, 0, 1, 1)
    popup.show_all()
    if not running_tests:
        popup.run()
        popup.destroy()


def read_info_from_man():
    """Read information on commands from the vimivrc.5 man page.

    Return:
        A dictionary containing command-names and information on them.
    """
    infodict = {}
    # Man page might have been installed as .5.gz by a package manager
    if os.path.isfile("/usr/share/man/man5/vimivrc.5"):
        with open("/usr/share/man/man5/vimivrc.5") as f:
            man_text = f.read()
    elif os.path.isfile("/usr/share/man/man5/vimivrc.5.gz"):
        with gzip.open("/usr/share/man/man5/vimivrc.5.gz") as f:
            man_text = f.read().decode()
    else:
        return {}
    # Loop over lines receiving command name and info
    lines = man_text.split("\n")
    for i, line in enumerate(man_text.split("\n")):
        if line.startswith("\\fB\\fC"):
            name = line.replace("\\fB\\fC", "").replace("\\fR", "")
            info = lines[i + 1].rstrip(".")  # Remove trailing periods
            infodict[name] = info
    return infodict


def expand_filenames(filename, filelist, command):
    """Expand % to filename and * to filelist in command."""
    # Escape spaces for the shell
    filename = filename.replace(" ", "\\\\\\\\ ")
    filelist = [f.replace(" ", "\\\\\\\\ ") for f in filelist]
    # Substitute % and * with escaping
    command = re.sub(r'(?<!\\)(%)', filename, command)
    command = re.sub(r'(?<!\\)(\*)', " ".join(filelist), command)
    command = re.sub(r'(\\)(?!\\)', "", command)
    return command


def get_boolean(value):
    """Convert a value to a boolean.

    Args:
        value: String value to convert.
    Return:
        bool: True if string.lower() in ["yes", "true"]. False otherwise.
    """
    return True if value.lower() in ["yes", "true"] else False


def get_int(value, allow_sign=False):
    """Convert a value to an integer.

    Args:
        value: String value to convert.
        allow_sign: If True, negative values are allowed.
    Return:
        int(value) if possible.
    """
    try:
        int_val = int(value)
    except ValueError:
        error = "Could not convert '%s' to int" % (value)
        raise StringConversionError(error)
    if int_val < 0 and not allow_sign:
        raise StringConversionError("Negative numbers are not supported.")
    return int_val


def get_float(value, allow_sign=False):
    """Convert a value to a float.

    Args:
        value: String value to convert.
        allow_sign: If True, negative values are allowed.
    Return:
        float(value) if possible.
    """
    try:
        float_val = float(value)
    except ValueError:
        error = "Could not convert '%s' to float" % (value)
        raise StringConversionError(error)
    if float_val < 0 and not allow_sign:
        raise StringConversionError("Negative numbers are not supported.")
    return float_val
