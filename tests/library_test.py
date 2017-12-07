# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test library.py for vimiv's test suite."""

import os
import tempfile
from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk
from vimiv.helpers import get_user_data_dir

from vimiv_testcase import VimivTestCase


class LibraryTest(VimivTestCase):
    """Test Library."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/"])
        cls.lib = cls.vimiv["library"]

    def setUp(self):
        self.directory = os.getcwd()

    def test_toggle(self):
        """Toggle the library."""
        self.lib.toggle()
        self.assertFalse(self.lib.is_focus())
        self.lib.toggle()
        self.assertTrue(self.lib.is_focus())

    def test_toggle_with_slideshow(self):
        """Toggle the library with running slideshow."""
        self.lib.toggle()
        self.vimiv["slideshow"].toggle()
        self.lib.toggle()
        self.assertFalse(self.vimiv["slideshow"].running)
        self.assertTrue(self.lib.is_focus())

    def test_file_select(self):
        """Select file in library."""
        # Directory by position
        path = Gtk.TreePath([self.lib.files.index("directory")])
        self.lib.file_select(None, path, None, False)
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.lib.move_up()
        # Library still focused
        self.assertTrue(self.lib.is_focus())
        # Image by position closing library
        path = Gtk.TreePath([self.lib.files.index("arch_001.jpg")])
        self.lib.file_select(None, path, None, True)
        expected_images = ["arch-logo.png", "arch_001.jpg", "symlink_to_image",
                           "vimiv.bmp", "vimiv.svg", "vimiv.tiff"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(self.vimiv.get_paths(), expected_images)
        open_image = self.vimiv.get_path()
        expected_image = os.path.abspath("arch_001.jpg")
        self.assertEqual(expected_image, open_image)
        # Library closed, image has focus
        self.assertFalse(self.lib.is_focus())
        self.assertFalse(self.lib.grid.is_focus())
        self.assertTrue(self.vimiv["main_window"].is_focus())

    def test_move_pos(self):
        """Move position in library."""
        # G
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "vimiv.tiff")
        # 3g
        self.vimiv["eventhandler"].set_num_str(3)
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "arch_001.jpg")
        self.assertFalse(self.vimiv["eventhandler"].get_num_str())
        # g
        self.lib.move_pos(False)
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # Throw an error
        self.vimiv["eventhandler"].set_num_str(300)
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.check_statusbar("WARNING: Unsupported index")

    def test_resize(self):
        """Resize library."""
        # Set to 200
        self.run_command("set library_width 200")
        self.assertEqual(200,
                         self.lib.get_size_request()[0])
        # Grow
        self.run_command("set library_width +20")
        self.assertEqual(220,
                         self.lib.get_size_request()[0])
        self.run_command("set library_width +30")
        self.assertEqual(250,
                         self.lib.get_size_request()[0])
        # Shrink
        self.run_command("set library_width -50")
        self.assertEqual(200,
                         self.lib.get_size_request()[0])
        # Grow and shrink via num_str
        self.run_command("2set library_width +20")
        self.assertEqual(240,
                         self.lib.get_size_request()[0])
        self.run_command("2set library_width -20")
        self.assertEqual(200,
                         self.lib.get_size_request()[0])
        self.assertFalse(self.vimiv["eventhandler"].get_num_str())
        # Too small
        self.run_command("set library_width -500")
        self.assertEqual(100,
                         self.lib.get_size_request()[0])
        self.assertGreater(self.settings["library_width"].get_value(), 0)
        # Throw errors
        self.run_command("set library_width hi")
        self.check_statusbar("ERROR: Could not convert 'hi' to int")
        self.run_command("set library_width +hi")
        self.check_statusbar("ERROR: Could not convert '+hi' to int")

    def test_scroll(self):
        """Scroll library."""
        # j
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.lib.scroll("j")
        self.assertEqual(self.vimiv.get_pos(True), "arch-logo.png")
        # k
        self.lib.scroll("k")
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # 3j
        self.vimiv["eventhandler"].set_num_str(3)
        self.lib.scroll("j")
        self.assertEqual(self.vimiv.get_pos(True), "directory")
        self.assertFalse(self.vimiv["eventhandler"].get_num_str())
        # l
        expected_path = os.path.abspath("directory")
        self.lib.scroll("l")
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.assertEqual(expected_path, os.getcwd())
        # h
        expected_path = os.path.abspath("..")
        self.lib.scroll("h")
        self.assertEqual(expected_path, os.getcwd())
        # Remember pos
        self.assertEqual(self.vimiv.get_pos(True), "directory")
        # Back to beginning
        self.vimiv["eventhandler"].set_num_str(3)
        self.lib.scroll("k")
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # Fail because of invalid argument
        self.lib.scroll("o")
        self.check_statusbar("ERROR: Invalid scroll direction o")

    def test_display_symlink(self):
        """Show real path of symbolic links in library as well."""
        index = self.lib.files.index("symlink_to_image")
        model = self.lib.get_model()
        markup_string = model[index][1]
        expected_string = "symlink_to_image  →  " \
            + os.path.realpath("symlink_to_image")
        self.assertEqual(markup_string, expected_string)
        # Also after a search
        self.vimiv["commandline"].enter_search()
        self.vimiv["commandline"].set_text("")
        markup_string = model[index][1]
        expected_string = "symlink_to_image  →  " \
            + os.path.realpath("symlink_to_image")
        self.assertEqual(markup_string, expected_string)

    def test_broken_symlink(self):
        """Reload library with broken symlink."""
        tmpfile = "temporary.png"
        sym = "broken_sym"
        os.system("cp arch-logo.png " + tmpfile)
        os.system("ln -s " + tmpfile + " " + sym)
        os.remove(tmpfile)
        self.lib.reload(".")
        self.assertNotIn(sym, self.lib.files)
        os.remove(sym)

    def test_move_up(self):
        """Move up into directory."""
        expected = "/".join(os.getcwd().split("/")[:-2])
        self.vimiv["eventhandler"].set_num_str(2)
        self.lib.move_up()
        self.assertEqual(os.getcwd(), expected)

    def test_empty_directory(self):
        """Move in and out of an empty directory."""
        tmpdir = tempfile.TemporaryDirectory(dir=get_user_data_dir())
        self.lib.move_up(tmpdir.name)
        self.assertEqual(os.getcwd(), tmpdir.name)
        self.check_statusbar("WARNING: Directory is empty")
        # Check if exception is caught properly
        self.lib.scroll("l")
        self.check_statusbar("ERROR: No file to select")
        self.lib.scroll("h")
        self.assertEqual(os.getcwd(), os.path.dirname(tmpdir.name))
        tmpdir.cleanup()

    def test_delete_undelete_library(self):
        """Delete and undelete a file from the library."""
        # Delete
        self.lib.move_pos(defined_pos=5)
        path = os.path.abspath(self.vimiv.get_pos(True))
        self.assertTrue(os.path.exists(path))
        self.vimiv["transform"].delete()
        self.assertFalse(os.path.exists(path))
        # Undelete
        self.vimiv["transform"].undelete(os.path.basename(path))
        self.assertTrue(os.path.exists(path))
        # Test index here so undelete is always called
        self.assertEqual(self.vimiv.get_pos(), 4)

    def tearDown(self):
        # Reopen and back to beginning
        self.lib.move_up(self.directory)
        if not self.lib.is_visible():
            self.lib.toggle()
        self.lib.set_cursor([Gtk.TreePath(0)], None, False)
        self.assertEqual(os.getcwd(), self.directory)


if __name__ == "__main__":
    main()
