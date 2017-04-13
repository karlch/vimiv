# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tests for the main file app.py for vimiv's test suite."""

import os
import sys
from unittest import main

from gi.repository import GLib

from vimiv_testcase import VimivTestCase


class AppTest(VimivTestCase):
    """App Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.tmpdir = ""

    def test_handle_local_options(self):
        """Handle commandline arguments."""
        # We need to catch information from standard output

        # Get version should print information to standard output and return 0
        option_version = GLib.VariantDict.new()
        bool_true = GLib.Variant("b", True)
        option_version.insert_value("version", bool_true)
        returncode = self.vimiv.do_handle_local_options(option_version)
        if not hasattr(sys.stdout, "getvalue"):
            self.fail("Need to run test in buffered mode.")
        # In pylint we do not run in buffered mode but this is checked with
        # hasattr just above.
        # pylint:disable=no-member
        output = sys.stdout.getvalue().strip()
        self.assertIn("vimiv", output)
        self.assertEqual(returncode, 0)
        # Set some different options and test if they were handled correctly
        options = GLib.VariantDict.new()
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

    def test_temp_basedir(self):
        """Using a temporary basedir."""
        # XDG_*_HOME directories should be in tmp
        self.assertIn("/tmp/vimiv-", os.getenv("XDG_CACHE_HOME"))
        self.assertIn("/tmp/vimiv-", os.getenv("XDG_CONFIG_HOME"))
        self.assertIn("/tmp/vimiv-", os.getenv("XDG_DATA_HOME"))
        # Thumbnail, Tag and Trash directory should contain tmp
        self.assertIn(
            "/tmp/",
            self.vimiv["thumbnail"].thumbnail_manager.thumbnail_store.base_dir)
        self.assertIn("/tmp/", self.vimiv["tags"].directory)
        trash_dir = self.vimiv["manipulate"].trash_manager.get_files_directory()
        info_dir = self.vimiv["manipulate"].trash_manager.get_info_directory()
        self.assertIn("/tmp/", trash_dir)
        self.assertIn("/tmp/", info_dir)
        # Create a tag in tmp as a simple test
        self.vimiv["tags"].write(["image1.py", "image2.py"], "tmptag")
        self.assertIn("tmptag", os.listdir(self.vimiv["tags"].directory))

    def test_quit_with_running_threads(self):
        """Quit vimiv with external threads running."""
        self.run_command("!sleep 0.2")
        self.vimiv.quit_wrapper()
        self.check_statusbar(
            "WARNING: Running external processes: sleep 0.2. Add ! to force.")

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit_wrapper()
        # Check if the temporary directory was deleted correctly
        cls.assertFalse(cls, os.path.exists(cls.tmpdir))
        os.chdir(cls.working_directory)


if __name__ == "__main__":
    main(buffer=True)
