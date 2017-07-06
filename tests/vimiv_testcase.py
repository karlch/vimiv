# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Wrapper of TestCase which sets up the vimiv class and quits it when done."""

import os
import time
from unittest import TestCase, main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk, GdkPixbuf
from vimiv.app import Vimiv
from vimiv.settings import settings


def refresh_gui(delay=0):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def compare_pixbufs(pb1, pb2):
    """Compare to pixbufs."""
    return pb1.get_pixels() == pb2.get_pixels()


def compare_files(file1, file2):
    """Directly compare two image files using GdkPixbuf."""
    pb1 = GdkPixbuf.Pixbuf.new_from_file(file1)
    pb2 = GdkPixbuf.Pixbuf.new_from_file(file2)
    return compare_pixbufs(pb1, pb2)


class VimivTestCase(TestCase):
    """Wrapper Class of TestCase."""

    @classmethod
    def setUpClass(cls):
        # Get set in init_test as setUpClass will be overridden
        cls.working_directory = ""
        cls.settings = settings
        cls.vimiv = Vimiv()
        cls.init_test(cls)

    def init_test(self, paths=None, to_set=None, values=None, debug=False):
        """Initialize a testable vimiv object saved as self.vimiv.

        Args:
            paths: Paths passed to vimiv.
            to_set: List of settings to be set.
            values: List of values for settings to be set.
        """
        self.working_directory = os.getcwd()
        # Create vimiv class with settings, paths, ...
        self.vimiv = Vimiv(True)  # True for running_tests
        self.settings = settings
        self.vimiv.debug = debug
        options = GLib.VariantDict.new()
        bool_true = GLib.Variant("b", True)
        options.insert_value("temp-basedir", bool_true)
        self.vimiv.do_handle_local_options(options)
        # Set the required settings
        if to_set:
            for i, setting in enumerate(to_set):
                self.settings.override(setting, values[i])
        self.vimiv.register()
        self.vimiv.do_startup(self.vimiv)
        if paths:
            # Create a list of Gio.Files for vimiv.do_open
            files = [Gio.File.new_for_path(path) for path in paths]
            self.vimiv.do_open(files, len(paths), "")
        else:
            self.vimiv.activate_vimiv(self.vimiv)

    def run_command(self, command, external=False):
        """Run a command in the command line.

        Args:
            command: The command to run.
            external: If True, run an external command and wait for it to
                finish.
        """
        self.vimiv["commandline"].enter(command)
        self.vimiv["commandline"].emit("activate")
        if external:
            while self.vimiv["commandline"].running_processes:
                self.vimiv["commandline"].running_processes[0].wait()
                time.sleep(0.001)

    def run_search(self, string):
        """Search for string from the command line."""
        self.vimiv["commandline"].enter_search()
        self.vimiv["commandline"].set_text("/" + string)
        self.vimiv["commandline"].emit("activate")

    def check_statusbar(self, expected_text):
        """Check statusbar for text."""
        statusbar_text = self.vimiv["statusbar"].get_message()
        self.assertEqual(expected_text, statusbar_text)

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)


if __name__ == "__main__":
    main()
