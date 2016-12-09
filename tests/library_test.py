#!/usr/bin/env python
# encoding: utf-8
"""Test library.py for vimiv's test suite."""

import os
from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv_testcase import VimivTestCase


class LibraryTest(VimivTestCase):
    """Test Library."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, paths="vimiv/testimages/")
        cls.lib = cls.vimiv["library"]

    def test_toggle(self):
        """Toggle the library."""
        self.lib.toggle()
        self.assertFalse(self.lib.treeview.is_focus())
        self.lib.toggle()
        self.assertTrue(self.lib.treeview.is_focus())

    def test_toggle_with_slideshow(self):
        """Toggle the library with running slideshow."""
        self.lib.toggle()
        self.vimiv["slideshow"].toggle()
        self.lib.toggle()
        self.assertFalse(self.vimiv["slideshow"].running)
        self.assertTrue(self.lib.treeview.is_focus())

    def test_file_select(self):
        """Select file in library."""
        # Directory by position
        path = Gtk.TreePath([self.lib.files.index("directory")])
        self.lib.file_select(None, path, None, False)
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.lib.move_up()
        # Library still focused
        self.assertTrue(self.lib.treeview.is_focus())
        # Image by position closing library
        path = Gtk.TreePath([self.lib.files.index("arch_001.jpg")])
        self.lib.file_select(None, path, None, True)
        expected_images = ["arch-logo.png", "arch_001.jpg", "symlink_to_image",
                           "vimiv.bmp", "vimiv.svg", "vimiv.tiff"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(self.vimiv.paths, expected_images)
        open_image = self.vimiv.paths[self.vimiv.index]
        expected_image = os.path.abspath("arch_001.jpg")
        self.assertEqual(expected_image, open_image)
        # Library closed, image has focus
        self.assertFalse(self.lib.treeview.is_focus())
        self.assertFalse(self.lib.grid.is_focus())
        self.assertTrue(self.vimiv["image"].scrolled_win.is_focus())
        # Reopen and back to beginning
        self.lib.toggle()
        self.lib.treeview.set_cursor([Gtk.TreePath(0)], None, False)

    def test_move_pos(self):
        """Move position in library."""
        # G
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "vimiv.tiff")
        # 3g
        self.vimiv["keyhandler"].num_str = "3"
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "arch_001.jpg")
        self.assertFalse(self.vimiv["keyhandler"].num_str)
        # g
        self.lib.move_pos(False)
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # Throw an error
        self.vimiv["keyhandler"].num_str = "300"
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        expected_message = "Warning: Unsupported index"
        received_message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_message, received_message)

    def test_resize(self):
        """Resize library."""
        # Set to 200
        self.lib.resize(None, True, 200)
        self.assertEqual(200,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Grow
        self.lib.resize(True)
        self.assertEqual(220,
                         self.lib.scrollable_treeview.get_size_request()[0])
        self.lib.resize(True, False, 30)
        self.assertEqual(250,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Shrink
        self.lib.resize(False, False, 50)
        self.assertEqual(200,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Too small
        self.lib.resize(False, False, 500)
        self.assertEqual(100,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Throw errors
        self.lib.resize(False, False, "hi")
        expected_message = "Library width must be an integer"
        received_message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_message, received_message)
        self.lib.resize(False, True, "hi")
        received_message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_message, received_message)

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
        self.vimiv["keyhandler"].num_str = "3"
        self.lib.scroll("j")
        self.assertEqual(self.vimiv.get_pos(True), "directory")
        self.assertFalse(self.vimiv["keyhandler"].num_str)
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
        self.vimiv["keyhandler"].num_str = "3"
        self.lib.scroll("k")
        self.assertEqual(self.vimiv.get_pos(True), "animation")


if __name__ == '__main__':
    main()
