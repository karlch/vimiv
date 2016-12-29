#!/usr/bin/env python
# encoding: utf-8
"""Test thumbnail.py for vimiv's test suite."""

import os
from unittest import main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv_testcase import VimivTestCase


def create_tuples(max_val, insert=None):
    """Create tuples for thumbnail sizes as powers of two starting from 64."""
    tuples = []
    value = 64
    while value <= max_val:
        tuples.append((value, value))
        value *= 2
    if insert:
        tuples.append((insert, insert))
    return sorted(tuples)


class ThumbnailTest(VimivTestCase):
    """Test thumbnail."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch-logo.png"])
        cls.thumb = cls.vimiv["thumbnail"]
        cls.thumb.size = (128, 128)
        cls.thumb.max_size = (256, 256)
        cls.thumb.sizes = [(64, 64), (128, 128), (256, 256)]

    def setUp(self):
        if self.thumb.toggled:
            self.thumb.toggle()
        self.vimiv.index = 0

    def test_toggle(self):
        """Toggle thumbnail mode."""
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.iconview.is_focus())
        self.thumb.toggle()
        self.assertTrue(self.thumb.toggled)
        self.assertTrue(self.thumb.iconview.is_focus())

    def test_iconview_clicked(self):
        """Select thumbnail."""
        self.thumb.toggle()
        path = Gtk.TreePath([1])
        self.thumb.iconview_clicked(None, path)
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.iconview.is_focus())
        expected_image = os.path.abspath("arch_001.jpg")
        received_image = self.vimiv.paths[self.vimiv.index]
        self.assertEqual(expected_image, received_image)

    def test_calculate_columns(self):
        """Calculate thumbnail columns."""
        self.thumb.toggle()
        expected_columns = int(800 / (self.thumb.size[0] + 30))
        received_columns = self.thumb.iconview.get_columns()
        self.assertEqual(expected_columns, received_columns)

    def test_reload(self):
        """Reload and name thumbnails."""
        self.thumb.toggle()
        liststore_iter = self.thumb.liststore.get_iter(0)
        name = self.thumb.liststore.get_value(liststore_iter, 1)
        self.assertEqual(name, "arch-logo")
        self.vimiv["mark"].mark()
        self.thumb.reload(self.vimiv.paths[0])
        new_liststore_iter = self.thumb.liststore.get_iter(0)
        name = self.thumb.liststore.get_value(new_liststore_iter, 1)
        self.assertEqual(name, "arch-logo [*]")

    def test_move(self):
        """Move in thumbnail mode."""
        self.thumb.toggle()
        for move_combo in [("l", "arch_001.jpg"), ("h", "arch-logo.png"),
                           ("j", "vimiv.tiff"), ("k", "arch-logo.png")]:
            self.thumb.move_direction(move_combo[0])
            expected_file = os.path.abspath(move_combo[1])
            received_file = self.vimiv.paths[self.vimiv.get_pos()]
            self.assertEqual(expected_file, received_file)

    def test_zoom(self):
        """Zoom in thumbnail mode."""
        self.thumb.toggle()
        self.assertEqual(self.thumb.size, (128, 128))
        self.thumb.zoom(True)
        self.assertEqual(self.thumb.size, (256, 256))
        pixbuf = list(self.thumb.liststore)[0][0]
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        scale = max(width, height)
        self.assertEqual(scale, 256)
        self.thumb.zoom(True)
        self.assertEqual(self.thumb.size, (256, 256))
        # This is the max size, one more zoom shouldn't change anything
        self.thumb.zoom(False)
        self.assertEqual(self.thumb.size, (128, 128))

    def test_thumb_sizes(self):
        """Parse sizes for thumbnails."""
        # Large max size
        self.thumb.max_size = (1000, 1000)
        self.thumb.set_sizes()
        expected_sizes = create_tuples(512)
        self.assertEqual(self.thumb.sizes, expected_sizes)
        # Small max size
        self.thumb.max_size = (128, 128)
        self.thumb.set_sizes()
        expected_sizes = create_tuples(128)
        self.assertEqual(self.thumb.sizes, expected_sizes)
        # Medium max size and insert a value
        self.thumb.max_size = (256, 256)
        self.thumb.size = (200, 200)
        self.thumb.set_sizes()
        expected_sizes = create_tuples(256, 200)
        self.assertEqual(self.thumb.sizes, expected_sizes)
        # To large size
        self.thumb.size = (1000, 1000)
        self.thumb.set_sizes()
        expected_sizes = create_tuples(256)
        self.assertEqual(self.thumb.sizes, expected_sizes)
        self.assertEqual(self.thumb.size, (256, 256))
        # Reset
        self.thumb.size = (128, 128)
        self.thumb.max_size = (256, 256)
        self.thumb.set_sizes()


if __name__ == '__main__':
    main()
