# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test fileactions.py for vimiv's test suite."""

import os
import shutil
from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import vimiv.fileactions as fileactions

from vimiv_testcase import VimivTestCase


class FileActionsTest(VimivTestCase):
    """Fileactions Tests."""

    @classmethod
    def setUpClass(cls):
        cls.compare_result = False  # Used for the clipboard comparison
        cls.test_directory = os.path.abspath("vimiv/")
        cls.init_test(cls, [cls.test_directory])

    def test_move_to_trash(self):
        """Move file to trash."""
        # TODO reactivate trash test
        return
        os.chdir("testimages/")
        shutil.copyfile("arch_001.jpg", "image_to_edit.jpg")
        filename = os.path.abspath("image_to_edit.jpg")
        files = [filename]
        fileactions.move_to_trash(files, self.trashdir)
        trashed_file = os.path.join(self.trashdir, "image_to_edit.jpg")
        self.assertTrue(os.path.isfile(trashed_file))
        # Repeat, to check if backing up works
        shutil.copyfile("arch_001.jpg", "image_to_edit.jpg")
        fileactions.move_to_trash(files, self.trashdir)
        trashed_file1 = os.path.join(self.trashdir, "image_to_edit.jpg.1")
        self.assertTrue(os.path.isfile(trashed_file1))
        shutil.copyfile("arch_001.jpg", "image_to_edit.jpg")
        fileactions.move_to_trash(files, self.trashdir)
        trashed_file2 = os.path.join(self.trashdir, "image_to_edit.jpg.2")
        self.assertTrue(os.path.isfile(trashed_file2))
        # Clear the files
        os.remove(trashed_file)
        os.remove(trashed_file1)

    def test_is_image(self):
        """Check whether file is an image."""
        os.chdir("testimages/")
        self.assertTrue(fileactions.is_image("arch_001.jpg"))
        self.assertFalse(fileactions.is_image("not_an_image.jpg"))

    def test_clear(self):
        """Clear Trash."""
        # TODO reactivate trash test
        return
        trashfile = os.path.join(self.trashdir, "foo")
        os.system("touch " + trashfile)
        self.assertIn("foo", os.listdir(self.trashdir))
        # Clear the file
        self.vimiv["fileextras"].clear("Trash")
        self.assertFalse(os.listdir(self.trashdir))

    def test_format_files(self):
        """Format files according to a formatstring."""
        shutil.copytree("testimages/", "testimages_to_format/")
        os.chdir("testimages_to_format")
        self.vimiv.quit()
        self.init_test(["arch_001.jpg"])
        self.vimiv["fileextras"].format_files("formatted_")
        files = [fil for fil in os.listdir() if "formatted_" in fil]
        files = sorted(files)
        expected_files = ["formatted_001.jpg", "formatted_002",
                          "formatted_003.bmp", "formatted_004.svg",
                          "formatted_005.tiff", "formatted_006.png"]
        self.assertEqual(files, expected_files)
        os.chdir("..")
        # Should not work without a path
        self.vimiv.paths = []
        self.vimiv["fileextras"].format_files("formatted_")
        self.check_statusbar("INFO: No files in path")
        # Should not work in library
        self.vimiv["library"].focus(True)
        self.vimiv["fileextras"].format_files("formatted_")
        self.check_statusbar("INFO: Format only works on opened image files")

    def test_format_files_with_exif(self):
        """Format files according to a formatstring with EXIF data."""
        # File contains exif data
        shutil.copytree("testimages/", "testimages_to_format/")
        os.chdir("testimages_to_format")
        self.vimiv.quit()
        self.init_test(["arch_001.jpg"])
        self.vimiv.paths = [os.path.abspath("arch_001.jpg")]
        self.vimiv["fileextras"].format_files("formatted_%Y_")
        self.assertIn("formatted_2016_001.jpg", os.listdir())
        # File does not contain exif data
        self.vimiv.paths = [os.path.abspath("arch-logo.png")]
        self.vimiv["fileextras"].format_files("formatted_%Y_")
        message = self.vimiv["statusbar"].left_label.get_text()
        self.assertIn("No exif data for", message)

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
        self.vimiv["fileextras"].toggle_clipboard()
        self.vimiv["fileextras"].copy_name(False)
        primary.request_text(compare_text, basename)
        self.assertTrue(self.compare_result)
        # Toggle back to clipboard and copy basename
        self.vimiv["fileextras"].toggle_clipboard()
        self.vimiv["fileextras"].copy_name(False)
        clipboard.request_text(compare_text, basename)
        self.assertTrue(self.compare_result)

    def tearDown(self):
        os.chdir(self.test_directory)
        if os.path.isdir("testimages_to_format"):
            shutil.rmtree("testimages_to_format")


if __name__ == "__main__":
    main()
