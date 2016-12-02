#!/usr/bin/env python3
# encoding: utf-8
"""Wrappers around standard library functions used in vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk

# Dictionary with all the scrolling
scrolltypes = {}
scrolltypes["h"] = (Gtk.ScrollType.STEP_BACKWARD, True)
scrolltypes["j"] = (Gtk.ScrollType.STEP_FORWARD, False)
scrolltypes["k"] = (Gtk.ScrollType.STEP_BACKWARD, False)
scrolltypes["l"] = (Gtk.ScrollType.STEP_FORWARD, True)
scrolltypes["H"] = (Gtk.ScrollType.START, True)
scrolltypes["J"] = (Gtk.ScrollType.END, False)
scrolltypes["K"] = (Gtk.ScrollType.START, False)
scrolltypes["L"] = (Gtk.ScrollType.END, True)

# A list of all external commands
pathenv = os.environ.get('PATH')
if pathenv is not None:
    executables = set()
    for bindir in pathenv.split(':'):
        try:
            executables |= set(["!" + exe for exe in os.listdir(bindir)])
        except OSError:
            continue
    external_commands = tuple(sorted(list(executables)))
else:
    external_commands = ()


def listdir_wrapper(path, show_hidden=False):
    """Reimplementation of os.listdir which mustn't show hidden files.

    Args:
        path: Path of the directory in which os.listdir is called.
        show_hidden: If true, show hidden files. Else do not.
    Return: Sorted list of files in path.
    """
    all_files = sorted(os.listdir(os.path.expanduser(path)))
    if show_hidden:
        return all_files
    else:
        return [fil for fil in all_files if not fil.startswith(".")]


def read_file(filename):
    """Read the content of a file into a list or create file.

    Args:
        filename: The name of the file to be read.
    Return: Content of filename in a list.
    """
    content = []
    try:
        fil = open(filename, "r")
        for line in fil:
            content.append(line.rstrip("\n"))
    except:
        fil = open(filename, "w")
        fil.write("")
    fil.close()
    return content


def sizeof_fmt(num):
    """Print size of a byte number in human-readable format.

    Args:
        num: Filesize in bytes.

    Return: Filesize in human-readable format.
    """
    for unit in ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            if abs(num) < 100:
                return "%3.1f%s" % (num, unit)
            else:
                return "%3.0f%s" % (num, unit)
        num /= 1024.0
    return "%.1f%s" % (num, 'Y')


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
    popup.add_button("Close", Gtk.ResponseType.CLOSE)
    message_label = Gtk.Label()
    message_label.set_text(message)
    message_label.set_hexpand(True)
    box = popup.get_child()
    box.set_border_width(12)
    grid = Gtk.Grid()
    grid.set_column_spacing(12)
    box.pack_start(grid, False, False, 12)
    icon_size = Gtk.IconSize(5)
    error_icon = Gtk.Image.new_from_icon_name("dialog-error", icon_size)
    grid.attach(error_icon, 0, 0, 1, 1)
    grid.attach(message_label, 1, 0, 1, 1)
    popup.show_all()
    if not running_tests:
        popup.run()
        popup.destroy()
