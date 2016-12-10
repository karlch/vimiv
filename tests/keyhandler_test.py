#!/usr/bin/env python
# encoding: utf-8
"""Tests keyhandler.py for vimiv's test suite."""

from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv_testcase import VimivTestCase


class KeyHandlerTest(VimivTestCase):
    """KeyHandler Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/"])

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
