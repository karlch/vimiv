# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tests window.py for vimiv's test suite."""

import os
from unittest import main, skipUnless
from vimiv_testcase import VimivTestCase, refresh_gui


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
        # Still not reliable
        # self.assertTrue(self.vimiv["window"].is_fullscreen)
        # Unfullscreen
        self.vimiv["window"].toggle_fullscreen()
        refresh_gui(0.05)
        # self.assertFalse(self.vimiv["window"].is_fullscreen)
        self.vimiv["window"].fullscreen()

    def test_scroll(self):
        """Scroll image or thumbnail."""
        # Error message
        self.vimiv["window"].scroll("m")
        self.assertEqual(self.vimiv["statusbar"].left_label.get_text(),
                         "ERROR: Invalid scroll direction m")

    @skipUnless(os.environ["DISPLAY"] == ":42", "Must run in Xvfb")
    def test_check_resize(self):
        """Resize window and check winsize."""
        self.assertEqual(self.vimiv["window"].winsize, (800, 600))
        self.vimiv["window"].resize(400, 300)
        refresh_gui()
        self.assertEqual(self.vimiv["window"].winsize, (400, 300))


if __name__ == '__main__':
    main()
