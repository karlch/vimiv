#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Class to handle log file for vimiv."""

import time
import os
import sys
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk


class Log():
    """Log file handler.

    Attributes:
        filename: Name of the log file.
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        self.filename = os.path.join(app.directory, "vimiv.log")
        self.terminal = sys.stderr
        # Redirect stderr in debug mode so it is written to the log file as well
        if app.debug:
            sys.stderr = self
        # Create a new log file at startup
        with open(self.filename, "w") as f:
            f.write("Vimiv log written to "
                    + self.filename.replace(os.environ["HOME"], "~")
                    + "\n")
        self.write_separator()
        # Header containing version and Gtk version
        self.write_message("Version", app["information"].get_version())
        self.write_message("Python", sys.version.split()[0])
        gtk_version = str(Gtk.get_major_version()) + "." \
            + str(Gtk.get_minor_version()) + "." \
            + str(Gtk.get_micro_version())
        self.write_message("GTK", gtk_version)
        self.write_separator()
        # Start time
        self.write_message("Started", "time")

    def write(self, message):
        """Write stderr message to log file and terminal."""
        print(message, end="")
        if "Traceback" in message:
            self.write_message("stderr", "")
        with open(self.filename, "a") as f:
            f.write(message)

    def flush(self):
        self.terminal.flush()

    def fileno(self):
        return self.terminal.fileno()

    def write_message(self, header, message):
        """Write information to the log file.

        Args:
            header: Title of the message, gets surrounded in [].
            message: Log message.
        """
        if "time" in message:
            now = [str(t) for t in time.localtime()[3:6]]
            formatted_time = ":".join(now)
            message = message.replace("time", formatted_time)
        message = message.replace("\n", "\n" + " " * 16)
        formatted_message = "%-15s %s\n" % ("[" + header + "]", message)
        with open(self.filename, "a") as f:
            f.write(formatted_message)

    def write_separator(self):
        """Write a neat 80 * # separator to the log file."""
        with open(self.filename, "a") as f:
            f.write("#" * 80 + "\n")
