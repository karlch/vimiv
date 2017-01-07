#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
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

    def test_add_number(self):
        """Add number to the numstr and clear it."""
        self.assertFalse(self.vimiv["keyhandler"].num_str)
        # Add a number
        self.vimiv["keyhandler"].num_append("2")
        self.assertEqual(self.vimiv["keyhandler"].num_str, "2")
        # Add another number, should change the timer_id
        id_before = self.vimiv["keyhandler"].timer_id
        self.vimiv["keyhandler"].num_append("3")
        id_after = self.vimiv["keyhandler"].timer_id
        self.assertNotEqual(id_before, id_after)
        self.assertEqual(self.vimiv["keyhandler"].num_str, "23")
        # Clear manually, GLib timeout should definitely work as well if the
        # code runs without errors
        self.vimiv["keyhandler"].num_clear()
        self.assertFalse(self.vimiv["keyhandler"].num_str)
        self.assertFalse(self.vimiv["keyhandler"].timer_id)

    def test_add_number_via_keypress(self):
        """Add a number to the numstr by keypress."""
        self.assertFalse(self.vimiv["keyhandler"].num_str)
        event = Gdk.Event().new(Gdk.EventType.KEY_PRESS)
        event.keyval = Gdk.keyval_from_name("2")
        self.vimiv["library"].treeview.emit("key_press_event", event)
        self.assertEqual(self.vimiv["keyhandler"].num_str, "2")
        # Clear as it might interfere
        self.vimiv["keyhandler"].num_clear()

    def test_key_press_modifier(self):
        """Press key with modifier."""
        before = self.vimiv["library"].show_hidden
        event = Gdk.Event().new(Gdk.EventType.KEY_PRESS)
        event.keyval = Gdk.keyval_from_name("h")
        event.state = Gdk.ModifierType.CONTROL_MASK
        self.vimiv["library"].treeview.emit("key_press_event", event)
        after = self.vimiv["library"].show_hidden
        self.assertNotEqual(before, after)


if __name__ == '__main__':
    main()
