# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tests for the main file app.py for vimiv's test suite."""

import os
import sys
from unittest import main

from gi.repository import GLib

from vimiv.app import Vimiv

from vimiv_testcase import VimivTestCase, refresh_gui


class AppTest(VimivTestCase):
    """App Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

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
        self.assertIn("/tmp/", self.vimiv["thumbnail"].get_cache_directory())
        self.assertIn("/tmp/", self.vimiv["tags"].directory)
        trash_dir = self.vimiv["manipulate"].trash_manager.get_files_directory()
        info_dir = self.vimiv["manipulate"].trash_manager.get_info_directory()
        self.assertIn("/tmp/", trash_dir)
        self.assertIn("/tmp/", info_dir)
        # Create a tag in tmp as a simple test
        self.vimiv["tags"].write(["image1.py", "image2.py"], "tmptag")
        self.assertIn("tmptag", os.listdir(self.vimiv["tags"].directory))

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit_wrapper()
        os.chdir(cls.working_directory)


class QuitTest(VimivTestCase):
    """Quit Tests."""

    def setUp(self):
        """Recreate vimiv for every run."""
        self.vimiv = Vimiv()
        self.init_test()

    def test_quit_with_running_threads(self):
        """Quit vimiv with external threads running."""
        self.run_command("!sleep 0.2")
        self.vimiv.quit_wrapper()
        self.check_statusbar(
            "WARNING: Running external processes: sleep 0.2. Add ! to force.")
        p = self.vimiv["commandline"].running_processes[0]
        # Kill the subprocess
        self.assertFalse(p.poll())
        self.vimiv.quit_wrapper(force=True)
        refresh_gui()
        self.assertEqual(p.poll(), -9)

    def test_clean_quit(self):
        """Quit vimiv and write history and log."""
        self.run_command("!:", external=True)
        self.vimiv.quit_wrapper()
        histfile = os.path.join(GLib.get_user_data_dir(), "vimiv", "history")
        logfile = os.path.join(GLib.get_user_data_dir(), "vimiv", "vimiv.log")
        with open(histfile) as f:
            content = f.readlines()
            self.assertEqual(content, [":!:\n"])
        with open(logfile) as f:
            content = f.readlines()
            self.assertIn("Exited", content[-1])

    def test_quit_with_edited_image(self):
        """Quit vimiv with an edited image."""
        # Fake a manipulation
        self.vimiv["manipulate"]._manipulations = {}
        self.vimiv.quit_wrapper()
        self.check_statusbar("WARNING: Image has been edited, add ! to force")
        # Force quit
        self.vimiv.quit_wrapper(force=True)
        refresh_gui()


if __name__ == "__main__":
    main(buffer=True)
