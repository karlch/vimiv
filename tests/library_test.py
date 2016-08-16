#!/usr/bin/env python
# encoding: utf-8
""" Test library.py for vimiv's test suite """

import os
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.parser import parse_config


class LibraryTest(TestCase):
    """ Test library """

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        os.chdir("vimiv")
        cls.settings = parse_config()
        cls.vimiv = v_main.Vimiv(cls.settings, "testimages", 0)
        cls.vimiv.main(True)
        cls.lib = cls.vimiv.library

    def test_toggle(self):
        """ Toggling of the library"""
        self.lib.toggle()
        self.assertFalse(self.lib.treeview.is_focus())
        self.lib.toggle()
        self.assertTrue(self.lib.treeview.is_focus())

    def test_file_select(self):
        """ Select file in library """
        # Directory by name
        self.lib.file_select(None, "directory", None, False)
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.lib.move_up()
        # Image by name
        self.lib.file_select(None, "arch-logo.png", None, False)
        expected_images = ["arch_001.jpg", "arch-logo.png", "symlink_to_image"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(self.vimiv.paths, expected_images)
        open_image = self.vimiv.paths[self.vimiv.index]
        expected_image = os.path.abspath("arch-logo.png")
        self.assertEqual(expected_image, open_image)
        # Library still focused
        self.assertTrue(self.lib.treeview.is_focus())
        # Image by position
        path = Gtk.TreePath([0])
        column = self.lib.treeview.get_column(1)
        self.lib.treeview.row_activated(path, column)
        self.assertEqual(self.vimiv.paths, expected_images)
        # Library closed, image has focus
        self.assertFalse(self.lib.treeview.is_focus())
        self.assertFalse(self.lib.toggled)
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        # Reopen and back to beginning
        self.lib.toggle()
        self.lib.treepos = 0

    def test_move_pos(self):
        """ Move position in library """
        # G
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")
        self.lib.move_pos()
        self.assertEqual(self.lib.files[self.lib.treepos], "symlink_to_image")
        # 3g
        self.vimiv.keyhandler.num_str = "3"
        self.lib.move_pos()
        self.assertEqual(self.lib.files[self.lib.treepos], "directory")
        self.assertFalse(self.vimiv.keyhandler.num_str)
        # g
        self.lib.move_pos(False)
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")
        # Throw an error
        self.vimiv.keyhandler.num_str = "300"
        self.lib.move_pos()
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")
        expected_message = "Warning: Unsupported index"
        received_message = self.vimiv.statusbar.left_label.get_text()
        self.assertEqual(expected_message, received_message)

    def test_resize(self):
        """ Resize library """
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
        received_message = self.vimiv.statusbar.left_label.get_text()
        self.assertEqual(expected_message, received_message)
        self.lib.resize(False, True, "hi")
        received_message = self.vimiv.statusbar.left_label.get_text()
        self.assertEqual(expected_message, received_message)

    def test_scroll(self):
        """ Scroll library """
        # j
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")
        self.lib.scroll("j")
        self.assertEqual(self.lib.files[self.lib.treepos], "arch-logo.png")
        # k
        self.lib.scroll("k")
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")
        # 2j
        self.vimiv.keyhandler.num_str = "2"
        self.lib.scroll("j")
        self.assertEqual(self.lib.files[self.lib.treepos], "directory")
        self.assertFalse(self.vimiv.keyhandler.num_str)
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
        self.assertEqual(self.lib.files[self.lib.treepos], "directory")
        # Back to beginning
        self.lib.scroll("k")
        self.lib.scroll("k")
        self.assertEqual(self.lib.files[self.lib.treepos], "arch_001.jpg")

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
