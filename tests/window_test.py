# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tests window.py for vimiv's test suite."""

import os
from unittest import main, skipUnless

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gdk

from vimiv_testcase import VimivTestCase, refresh_gui


class WindowTest(VimivTestCase):
    """Window Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/"])

    def test_fullscreen(self):
        """Toggle fullscreen."""
        # Start without fullscreen
        self.assertFalse(self._is_fullscreen())
        # Fullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        # Still not reliable
        # self.assertTrue(self._is_fullscreen())
        # Unfullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        # self.assertFalse(self.vimiv["window"].is_fullscreen)
        self.vimiv["window"].fullscreen()

    def _is_fullscreen(self):
        state = self.vimiv["window"].get_window().get_state()
        return True if state & Gdk.WindowState.FULLSCREEN else False

    @skipUnless(os.getenv("DISPLAY") == ":42", "Must run in Xvfb")
    def test_check_resize(self):
        """Resize window and check winsize."""
        self.assertEqual(self.vimiv["window"].winsize, (800, 600))
        self.vimiv["window"].resize(400, 300)
        refresh_gui()
        self.assertEqual(self.vimiv["window"].winsize, (400, 300))


if __name__ == "__main__":
    main()
