#!/usr/bin/env python
# encoding: utf-8
"""Switching between modes tests for vimiv's test suite."""


import os
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.parser import parse_config
from vimiv.fileactions import populate


class ModeSwitchTestImage(TestCase):
    """Mode Switching Tests starting from image mode."""

    @classmethod
    def setUpClass(cls):
        cls.initial_directory = os.getcwd()
        os.chdir("vimiv/testimages")
        cls.settings = parse_config()
        paths, index = populate(["arch_001.jpg"])
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.vimiv.main()

    def setUp(self):
        self.working_directory = os.getcwd()

    def test_image_library(self):
        """Switch between image and library mode."""
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertFalse(self.vimiv.library.treeview.is_visible())

        self.vimiv.library.toggle()
        self.assertFalse(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.library.treeview.is_visible())
        self.assertTrue(self.vimiv.library.treeview.is_focus())

        self.vimiv.library.toggle()
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertFalse(self.vimiv.library.treeview.is_visible())

    def test_image_thumbnail(self):
        """Switch between image and thumbnail mode."""
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertEqual(self.vimiv.image.scrolled_win.get_child(),
                         self.vimiv.image.viewport)

        self.vimiv.thumbnail.toggle()
        self.assertTrue(self.vimiv.thumbnail.iconview.is_focus())
        self.assertEqual(self.vimiv.image.scrolled_win.get_child(),
                         self.vimiv.thumbnail.iconview)
        self.assertEqual(self.vimiv.window.last_focused, "im")

        self.vimiv.thumbnail.toggle()
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertEqual(self.vimiv.image.scrolled_win.get_child(),
                         self.vimiv.image.viewport)

    def test_image_manipulate(self):
        """Switch between image and manipulate mode."""
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertFalse(self.vimiv.manipulate.scrolled_win.is_visible())

        self.vimiv.manipulate.toggle()
        self.assertTrue(self.vimiv.manipulate.scrolled_win.is_visible())
        self.assertTrue(self.vimiv.manipulate.scale_bri.is_focus())

        self.vimiv.manipulate.toggle()
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertFalse(self.vimiv.manipulate.scrolled_win.is_visible())

    def tearDown(self):
        os.chdir(self.working_directory)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.initial_directory)


class ModeSwitchTestLibrary(TestCase):
    """Mode Switching Tests starting from library mode."""

    @classmethod
    def setUpClass(cls):
        cls.initial_directory = os.getcwd()
        os.chdir("vimiv/testimages")
        cls.settings = parse_config()
        cls.vimiv = v_main.Vimiv(cls.settings, [], 0)
        cls.vimiv.main()

    def setUp(self):
        self.working_directory = os.getcwd()

    def test_library_image(self):
        """Switch between library and image mode."""
        self.assertTrue(self.vimiv.library.treeview.is_focus())
        path = Gtk.TreePath([self.vimiv.library.files.index("arch-logo.png")])
        self.vimiv.library.file_select(None, path, None, True)
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertFalse(self.vimiv.library.treeview.is_visible())

        self.vimiv.library.toggle()
        self.assertTrue(self.vimiv.library.treeview.is_focus())
        self.assertTrue(self.vimiv.library.treeview.is_visible())

    def test_library_thumbnail(self):
        """Switch between library and thumbnail mode."""
        self.assertTrue(self.vimiv.library.treeview.is_focus())
        self.vimiv.thumbnail.toggle()
        self.assertTrue(self.vimiv.thumbnail.iconview.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_visible())
        self.assertEqual(self.vimiv.image.scrolled_win.get_child(),
                         self.vimiv.thumbnail.iconview)
        self.assertEqual(self.vimiv.window.last_focused, "lib")

        self.vimiv.thumbnail.toggle()
        self.assertTrue(self.vimiv.library.treeview.is_focus())
        self.assertNotEqual(self.vimiv.image.scrolled_win.get_child(),
                            self.vimiv.thumbnail.iconview)

    def tearDown(self):
        os.chdir(self.working_directory)
        self.vimiv.library.reload(os.getcwd())

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.initial_directory)


if __name__ == '__main__':
    main()
