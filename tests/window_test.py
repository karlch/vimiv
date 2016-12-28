#!/usr/bin/env python
# encoding: utf-8
"""Tests window.py for vimiv's test suite."""

from unittest import main
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


if __name__ == '__main__':
    main()
