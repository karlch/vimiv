#!/usr/bin/env python
# encoding: utf-8
"""Tests events.py for vimiv's test suite."""

import time
from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv_testcase import VimivTestCase


def refresh_gui(delay=0):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


class EventTest(VimivTestCase):
    """Event Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, paths="vimiv/testimages/")

    def test_fullscreen(self):
        """Toggle fullscreen."""
        # Start without fullscreen
        self.assertFalse(self.vimiv["window"].is_fullscreen)
        # Fullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        # TODO these are not reliable
        # self.assertTrue(self.vimiv["window"].is_fullscreen)
        # Unfullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        # self.assertFalse(self.vimiv["window"].is_fullscreen)
        self.vimiv["window"].fullscreen()

    def test_key_press(self):
        """Press key."""
        self.vimiv["library"].file_select(None, Gtk.TreePath(1), None, True)
        image_before = self.vimiv.paths[self.vimiv.index]
        event = Gdk.Event().new(Gdk.EventType.KEY_PRESS)
        event.keyval = Gdk.keyval_from_name("n")
        self.vimiv["image"].scrolled_win.emit("key_press_event", event)
        image_after = self.vimiv.paths[self.vimiv.index]
        self.assertNotEqual(image_before, image_after)
        event.keyval = Gdk.keyval_from_name("O")
        self.vimiv["image"].scrolled_win.emit("key_press_event", event)
        self.assertTrue(self.vimiv["library"].treeview.is_focus())


if __name__ == '__main__':
    main()
