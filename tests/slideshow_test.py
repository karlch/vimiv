#!/usr/bin/env python
# encoding: utf-8
"""Test slideshow.py for vimiv's test suite."""

from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv.fileactions import populate
from vimiv_testcase import VimivTestCase


def refresh_gui(vimiv=None):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        delay: Time to wait before refreshing.
    """
    current_pos = vimiv.index
    while current_pos == vimiv.index:
        Gtk.main_iteration_do(False)


class SlideshowTest(VimivTestCase):
    """Slideshow Tests."""

    @classmethod
    def setUpClass(cls):
        paths, index = populate(["vimiv/testimages/arch_001.jpg"])
        cls.init_test(cls, paths=paths, index=index)
        cls.slideshow = cls.vimiv["slideshow"]

    def test_toggle(self):
        """Toggle slideshow."""
        self.assertFalse(self.slideshow.running)
        self.slideshow.toggle()
        self.assertTrue(self.slideshow.running)
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        # Throw some errors
        self.vimiv["thumbnail"].toggled = True
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv["thumbnail"].toggled = False
        paths_before = self.vimiv.paths
        self.vimiv.paths = []
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv.paths = paths_before

    def test_set_delay(self):
        """Set slideshow delay."""
        self.assertEqual(self.slideshow.delay, 2.0)
        self.slideshow.set_delay(3.0)
        self.assertEqual(self.slideshow.delay, 3.0)
        self.slideshow.set_delay(None, "-")
        self.assertEqual(self.slideshow.delay, 2.8)
        self.slideshow.set_delay(None, "+")
        self.assertEqual(self.slideshow.delay, 3.0)
        # Set via toggle
        self.vimiv["keyhandler"].num_str = "2"
        self.slideshow.toggle()
        self.assertEqual(self.slideshow.delay, 2.0)

    def test_running(self):
        """Check if slideshow runs correctly."""
        self.assertEqual(self.vimiv.index, 0)
        self.slideshow.toggle()
        # Set delay when running
        self.slideshow.set_delay(0.001)
        self.assertEqual(self.slideshow.delay, 0.001)
        for i in range(1, 6):
            refresh_gui(self.vimiv)
            self.assertEqual(self.vimiv.index, i)
        refresh_gui(self.vimiv)
        self.assertEqual(self.vimiv.index, 0)

    def tearDown(self):
        if self.slideshow.running:
            self.slideshow.toggle()
        self.slideshow.delay = 2.0


if __name__ == '__main__':
    main()
