#!/usr/bin/env python
# encoding: utf-8
"""Tests events.py for vimiv's test suite."""

import os
import time
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.parser import parse_config


def refresh_gui(delay=0):
    """Refresh the gui as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


class EventTest(TestCase):
    """Event Tests."""

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        os.chdir("vimiv/testimages")
        cls.settings = parse_config()
        cls.vimiv = v_main.Vimiv(cls.settings, [], 0)
        cls.vimiv.main()

    def test_fullscreen(self):
        """Toggle fullscreen"""
        # Start without fullscreen
        self.assertFalse(self.vimiv.window.fullscreen)
        # Fullscreen
        self.vimiv.window.toggle_fullscreen()
        refresh_gui(0.05)
        self.assertTrue(self.vimiv.window.fullscreen)
        # Unfullscreen
        self.vimiv.window.toggle_fullscreen()
        refresh_gui(0.05)
        self.assertFalse(self.vimiv.window.fullscreen)
        self.vimiv.fullscreen()

    def test_key_press(self):
        self.vimiv.library.file_select(None, Gtk.TreePath(1), None, True)
        image_before = self.vimiv.paths[self.vimiv.index]
        os.system("xdotool key n")
        refresh_gui(0.05)
        image_after = self.vimiv.paths[self.vimiv.index]
        self.assertNotEqual(image_before, image_after)
        os.system("xdotool key O")
        refresh_gui(0.05)
        self.assertTrue(self.vimiv.library.treeview.is_focus())

    @classmethod
    def tearDownClass(self):
        os.chdir(self.working_directory)


if __name__ == '__main__':
    main()
