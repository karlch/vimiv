#!/usr/bin/env python
# encoding: utf-8
"""Wrapper of TestCase which sets up the vimiv class and quits it when done."""

import os
import time
# from math import sqrt
from unittest import TestCase, main
from PIL import Image
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk
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
    image1 = Image.open(file1)
    image2 = Image.open(file2)
    return image1 == image2

class VimivTestCase(TestCase):
    """Wrapper Class of TestCase."""

    @classmethod
    def setUpClass(cls):
        # Get set in init_test as setUpClass will be overridden
        cls.working_directory = ""
        cls.vimiv = Vimiv("org.vimiv")
        cls.init_test(cls)

    def init_test(self, paths=None, key1=None, key2=None, val=None):
        """Initialize a testable vimiv object saved as self.vimiv.

        Args:
            paths: Paths passed to vimiv.
            key1: List of keys of the sections for settings to be set.
            key2: List of keys for settings to be set.
            val: List of values for settings to be set.
        """
        self.working_directory = os.getcwd()
        # A new ID for every generated vimiv class
        vimiv_id = "org.vimiv" + str(time.time()).replace(".", "")
        # Create vimiv class with settings, paths, ...
        self.vimiv = Vimiv(vimiv_id)
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

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
