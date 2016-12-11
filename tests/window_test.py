#!/usr/bin/env python
# encoding: utf-8
"""Tests window.py for vimiv's test suite."""

import time
from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv_testcase import VimivTestCase


def refresh_gui(delay=0):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


class WindowTest(VimivTestCase):
    """Window Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/"])

    def test_fullscreen(self):
        """Toggle fullscreen."""
        # Start without fullscreen
        self.assertFalse(self.vimiv["window"].is_fullscreen)
        # Fullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        self.assertTrue(self.vimiv["window"].is_fullscreen)
        # Unfullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        self.assertFalse(self.vimiv["window"].is_fullscreen)
        self.vimiv["window"].fullscreen()


if __name__ == '__main__':
    main()
