#!/usr/bin/env python
# encoding: utf-8
""" Test thumbnail.py for vimiv's test suite """

import os
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.fileactions import populate
from vimiv.parser import parse_config


class ThumbnailTest(TestCase):
    """ Test thumbnail """

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        cls.settings = parse_config()
        paths, index = populate(["testimages/arch-logo.png"])
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.vimiv.main(True)
        cls.thumb = cls.vimiv.thumbnail

    def setUp(self):
        if self.thumb.toggled:
            self.thumb.toggle()
        self.thumb.pos = 0
        self.vimiv.index = 0

    def test_toggle(self):
        """ Toggling thumbnail mode """
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.iconview.is_focus())
        self.thumb.toggle()
        self.assertTrue(self.thumb.toggled)
        self.assertTrue(self.thumb.iconview.is_focus())

    def test_iconview_clicked(self):
        """ Select thumbnail """
        self.thumb.toggle()
        path = Gtk.TreePath([1])
        self.thumb.iconview_clicked(None, path)
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.iconview.is_focus())
        expected_image = os.path.abspath("arch_001.jpg")
        received_image = self.vimiv.paths[self.vimiv.index]
        self.assertEqual(expected_image, received_image)

    def test_calculate_columns(self):
        """ Calculate thumbnail columns """
        self.thumb.toggle()
        expected_columns = int(800 / (self.thumb.size[0] + 30))
        received_columns = self.thumb.iconview.get_columns()
        self.assertEqual(expected_columns, received_columns)

    def test_reload(self):
        """ Reload and name thumbnails """
        self.thumb.toggle()
        liststore_iter = self.thumb.liststore.get_iter(0)
        name = self.thumb.liststore.get_value(liststore_iter, 1)
        self.assertEqual(name, "arch-logo")
        self.vimiv.mark.mark()
        self.thumb.reload(self.vimiv.paths[0], 0)
        new_liststore_iter = self.thumb.liststore.get_iter(0)
        name = self.thumb.liststore.get_value(new_liststore_iter, 1)
        self.assertEqual(name, "arch-logo [*]")

    def test_move(self):
        """ Move in thumbnail mode """
        self.thumb.toggle()
        print(self.vimiv.paths)
        print(self.thumb.pos)
        for move_combo in [("l", "arch_001.jpg"), ("h", "arch-logo.png"),
                           ("j", "symlink_to_image"), ("k", "arch-logo.png")]:
            self.thumb.move(move_combo[0])
            expected_file = os.path.abspath(move_combo[1])
            received_file = self.vimiv.paths[self.thumb.pos]
            self.assertEqual(expected_file, received_file)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
