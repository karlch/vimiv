# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test fileactions.py for vimiv's test suite."""

import os
import shutil
from unittest import main

import vimiv.fileactions as fileactions
from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

from vimiv_testcase import VimivTestCase


class FormatTest(VimivTestCase):
    """Test formatting files."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/"])

    def test_format_files(self):
        """Format files according to a formatstring."""
        shutil.copytree("testimages/", "testimages_to_format/")
        self.run_command("./testimages_to_format/arch-logo.png")
        self.vimiv["library"].toggle()
        self.vimiv["fileextras"].format_files("formatted_")
        files = [fil for fil in os.listdir() if "formatted_" in fil]
        files = sorted(files)
        expected_files = ["formatted_001.png", "formatted_002.jpg",
                          "formatted_003", "formatted_004.bmp",
                          "formatted_005.svg", "formatted_006.tiff"]
        for fil in expected_files:
            self.assertIn(fil, files)
        # Should not work without a path
        self.vimiv.populate([])
        self.vimiv["fileextras"].format_files("formatted_")
        self.check_statusbar("INFO: No files in path")

    def test_format_files_with_exif(self):
        """Format files according to a formatstring with EXIF data."""
        os.mkdir("testimages_to_format")
        shutil.copyfile("testimages/arch_001.jpg",
                        "testimages_to_format/arch_001.jpg")
        self.run_command("./testimages_to_format/arch_001.jpg")
        self.vimiv["library"].toggle()
        self.vimiv["fileextras"].format_files("formatted_%Y_")
        self.assertIn("formatted_2016_001.jpg", os.listdir())

    def test_fail_format_files_with_exif(self):
        """Run format with exif on a file that has no exif data."""
        os.mkdir("testimages_to_format")
        shutil.copyfile("testimages/arch-logo.png",
                        "testimages_to_format/arch-logo.png")
        self.run_command("./testimages_to_format/arch-logo.png")
        self.vimiv["library"].toggle()
        self.vimiv["fileextras"].format_files("formatted_%Y_")
        message = self.vimiv["statusbar"].get_message()
        self.assertIn("No exif data for", message)

    def tearDown(self):
        # Should not work in library
        if os.path.basename(os.getcwd()) != "vimiv":
            self.vimiv["library"].move_up()
            self.vimiv["fileextras"].format_files("formatted_")
            self.check_statusbar(
                "INFO: Format only works on opened image files")
        # Remove generated paths
        if os.path.isdir("testimages_to_format"):
            shutil.rmtree("testimages_to_format")


class ClipboardTest(VimivTestCase):
    """Test copying to clipboard."""

    @classmethod
    def setUpClass(cls):
        cls.compare_result = False  # Used for the clipboard comparison
        cls.init_test(cls, ["vimiv/"])

    def test_clipboard(self):
        """Copy image name to clipboard."""
        def compare_text(clipboard, text, expected_text):
            self.compare_result = False
            self.compare_result = text == expected_text
        name = self.vimiv.get_pos(True)
        basename = os.path.basename(name)
        abspath = os.path.abspath(name)
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        primary = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        # Copy basename and abspath to clipboard
        self.vimiv["fileextras"].copy_name(False)
        # Check if the info message is displayed correctly
        self.check_statusbar("INFO: Copied " + basename + " to clipboard")
        clipboard.request_text(compare_text, basename)
        self.assertTrue(self.compare_result)
        self.vimiv["fileextras"].copy_name(True)
        clipboard.request_text(compare_text, abspath)
        self.assertTrue(self.compare_result)
        # Toggle to primary and copy basename
        self.run_command("set copy_to_primary!")
        self.vimiv["fileextras"].copy_name(False)
        primary.request_text(compare_text, basename)
        self.assertTrue(self.compare_result)
        # Toggle back to clipboard and copy basename
        self.run_command("set copy_to_primary!")
        self.vimiv["fileextras"].copy_name(False)
        clipboard.request_text(compare_text, basename)
        self.assertTrue(self.compare_result)


class FileActionsTest(VimivTestCase):
    """Fileactions Tests."""

    @classmethod
    def setUpClass(cls):
        cls.compare_result = False  # Used for the clipboard comparison
        cls.init_test(cls, ["vimiv/"])

    def test_is_image(self):
        """Check whether file is an image."""
        self.assertTrue(fileactions.is_image("testimages/arch_001.jpg"))
        self.assertFalse(fileactions.is_image("testimages/not_an_image.jpg"))


if __name__ == "__main__":
    main()
