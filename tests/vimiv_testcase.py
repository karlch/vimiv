# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Wrapper of TestCase which sets up the vimiv class and quits it when done."""

import os
import time
from unittest import TestCase, main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk
from PIL import Image
from vimiv.app import Vimiv


def refresh_gui(delay=0):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def compare_images(file1, file2):
    """Directly compare two images using PIL."""
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    return image1 == image2


class VimivTestCase(TestCase):
    """Wrapper Class of TestCase."""

    @classmethod
    def setUpClass(cls):
        # Get set in init_test as setUpClass will be overridden
        cls.working_directory = ""
        cls.vimiv = Vimiv()
        cls.init_test(cls)

    def init_test(self, paths=None, key1=None, key2=None, val=None,
                  debug=False):
        """Initialize a testable vimiv object saved as self.vimiv.

        Args:
            paths: Paths passed to vimiv.
            key1: List of keys of the sections for settings to be set.
            key2: List of keys for settings to be set.
            val: List of values for settings to be set.
        """
        self.working_directory = os.getcwd()
        # Create vimiv class with settings, paths, ...
        self.vimiv = Vimiv(True)  # True for running_tests
        self.vimiv.debug = debug
        self.vimiv.do_handle_local_options(GLib.VariantDict())
        # Set the required settings
        if key1:
            for i, section in enumerate(key1):
                self.vimiv.settings[section][key2[i]] = val[i]
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
        self.vimiv["commandline"].focus(command)
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        if external:
            while self.vimiv["commandline"].running_processes:
                self.vimiv["commandline"].running_processes[0].wait()
                time.sleep(0.001)

    def run_search(self, string):
        """Search for string from the command line."""
        self.vimiv["commandline"].entry.set_text("/" + string)
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)

    def check_statusbar(self, expected_text):
        """Check statusbar for text."""
        statusbar_text = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_text, statusbar_text)

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)


if __name__ == "__main__":
    main()
