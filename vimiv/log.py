# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Class to handle log file for vimiv."""

import os
import sys
import time

from gi.repository import Gtk, GLib


class Log():
    """Log file handler.

    Attributes:
        _filename: Name of the log file.
        _terminal: sys.stderr to interact with
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        datadir = os.path.join(GLib.get_user_data_dir(), "vimiv")
        os.makedirs(datadir, exist_ok=True)
        self._filename = os.path.join(datadir, "vimiv.log")
        self._terminal = sys.stderr
        # Redirect stderr in debug mode so it is written to the log file as well
        if app.debug:
            sys.stderr = self
        # Create a new log file at startup
        with open(self._filename, "w") as f:
            f.write("Vimiv log written to "
                    + self._filename.replace(os.getenv("HOME"), "~")
                    + "\n")
        self._write_separator()
        # Header containing version and Gtk version
        self.write_message("Version", app["information"].get_version())
        self.write_message("Python", sys.version.split()[0])
        gtk_version = str(Gtk.get_major_version()) + "." \
            + str(Gtk.get_minor_version()) + "." \
            + str(Gtk.get_micro_version())
        self.write_message("GTK", gtk_version)
        self._write_separator()
        # Start time
        self.write_message("Started", "time")

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
        with open(self._filename, "a") as f:
            f.write(formatted_message)

    def write(self, message):
        """Write stderr message to log file and terminal."""
        print(message, end="")
        if "Traceback" in message:
            self.write_message("stderr", "")
        with open(self._filename, "a") as f:
            f.write(message)

    def flush(self):
        self._terminal.flush()

    def fileno(self):
        return self._terminal.fileno()

    def _write_separator(self):
        """Write a neat 80 * # separator to the log file."""
        with open(self._filename, "a") as f:
            f.write("#" * 80 + "\n")
