#!/usr/bin/env python
# encoding: utf-8
"""Tests for the main file app.py for vimiv's test suite."""

from unittest import main
# from gi import require_version
# require_version('GLib', '3.0')
from gi.repository import GLib
from vimiv_testcase import VimivTestCase


class AppTest(VimivTestCase):
    """App Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def test_handle_local_options(self):
        """Handle commandline arguments."""
        # Get version should return zero and do nothing else
        option_version = GLib.VariantDict()
        bool_true = GLib.Variant("b", True)
        option_version.insert_value("version", bool_true)
        returncode = self.vimiv.do_handle_local_options(option_version)
        self.assertEqual(returncode, 0)
        # Set some different options and test if they were handled correctly
        options = GLib.VariantDict()
        options.insert_value("shuffle", bool_true)
        double_22 = GLib.Variant("d", 2.2)
        options.insert_value("slideshow-delay", double_22)
        string_geom = GLib.Variant("s", "400x400")
        options.insert_value("geometry", string_geom)
        returncode = self.vimiv.do_handle_local_options(options)
        self.assertEqual(returncode, -1)
        self.assertTrue(self.vimiv.settings["GENERAL"]["shuffle"])
        self.assertFalse(self.vimiv.settings["GENERAL"]["start_slideshow"])
        self.assertEqual(self.vimiv.settings["GENERAL"]["slideshow_delay"], 2.2)
        self.assertEqual(self.vimiv.settings["GENERAL"]["geometry"], "400x400")


if __name__ == "__main__":
    main()
