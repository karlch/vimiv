# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test slideshow.py for vimiv's test suite."""

from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk

from vimiv_testcase import VimivTestCase


def refresh_gui(vimiv=None):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        vimiv: Vimiv class to receive slideshow index.
    """
    current_pos = vimiv.get_index()
    while current_pos == vimiv.get_index():
        Gtk.main_iteration_do(False)


class SlideshowTest(VimivTestCase):
    """Slideshow Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch_001.jpg"])
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
        paths_before = self.vimiv.get_paths()
        self.vimiv.populate([])
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv.paths = paths_before

    def test_set_delay(self):
        """Set slideshow delay."""
        self.assertEqual(self._get_delay(), 2.0)
        self.run_command("set slideshow_delay 3.0")
        self.assertEqual(self._get_delay(), 3.0)
        self.run_command("set slideshow_delay -0.2")
        self.assertAlmostEqual(self._get_delay(), 2.8)
        self.run_command("set slideshow_delay +0.4")
        self.assertAlmostEqual(self._get_delay(), 3.2)
        # Shrink with num_str
        self.run_command("2set slideshow_delay -0.2")
        self.assertAlmostEqual(self._get_delay(), 2.8)
        # Set via toggle
        self.vimiv["eventhandler"].set_num_str(2)
        self.slideshow.toggle()
        self.assertEqual(self._get_delay(), 2.0)
        # Set to a too small value
        self.run_command("set slideshow_delay 0.1")
        self.assertEqual(self._get_delay(), 0.5)
        # Fail because of invalid argument
        self.run_command("set slideshow_delay value")
        self.check_statusbar("ERROR: Could not convert 'value' to float")

    def test_running(self):
        """Check if slideshow runs correctly."""
        self.assertEqual(self.vimiv.get_index(), 1)
        self.slideshow.toggle()
        # Set delay when running
        self.run_command("set slideshow_delay 0.5")
        for i in range(2, 4):
            refresh_gui(self.vimiv)
            self.assertEqual(self.vimiv.get_index(), i)
        refresh_gui(self.vimiv)
        self.run_command("set slideshow_delay 2.0")

    def test_get_formatted_delay(self):
        """Read out the formatted delay from the slideshow."""
        output = self.slideshow.get_formatted_delay()
        self.assertIn("2.0s", output)

    def _get_delay(self):
        return self.settings["slideshow_delay"].get_value()

    def tearDown(self):
        if self.slideshow.running:
            self.slideshow.toggle()
        self.settings.override("slideshow_delay", "2.0")


if __name__ == "__main__":
    main()
