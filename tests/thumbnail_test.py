# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test thumbnail.py for vimiv's test suite."""

import os
from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk

from vimiv_testcase import VimivTestCase, refresh_gui


class ThumbnailTest(VimivTestCase):
    """Test thumbnail."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch-logo.png"])
        cls.thumb = cls.vimiv["thumbnail"]

    def setUp(self):
        self.thumb.toggle()

    def test_toggle(self):
        """Toggle thumbnail mode."""
        self.assertTrue(self.thumb.toggled)
        self.assertTrue(self.thumb.is_focus())
        self.thumb.toggle()
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.is_focus())

    def test_iconview_clicked(self):
        """Select thumbnail."""
        path = Gtk.TreePath([1])
        self.thumb.emit("item-activated", path)
        self.assertFalse(self.thumb.toggled)
        self.assertFalse(self.thumb.is_focus())
        expected_image = os.path.abspath("arch_001.jpg")
        received_image = self.vimiv.get_path()
        self.assertEqual(expected_image, received_image)

    def test_calculate_columns(self):
        """Calculate thumbnail columns."""
        expected_columns = int(800 / (self.thumb.get_zoom_level()[0] + 30))
        received_columns = self.thumb.get_columns()
        self.assertEqual(expected_columns, received_columns)

    def test_reload(self):
        """Reload and name thumbnails."""
        path = self.vimiv.get_pos(True)
        expected_name, _ = os.path.splitext(path)
        expected_name = os.path.basename(expected_name)
        name = self._get_thumbnail_name()
        self.assertEqual(expected_name, name)
        self.vimiv["mark"].mark()
        self.thumb.reload(path)
        name = self._get_thumbnail_name()
        self.assertEqual(name, expected_name + " [*]")

    def test_move(self):
        """Move in thumbnail mode."""
        start = self.vimiv.get_pos()
        self.assertGreaterEqual(self.thumb.get_columns(), 6)
        # All items are in the same row
        # l moves 1 to the right
        self.thumb.move_direction("l")
        self.assertEqual(self.vimiv.get_paths()[start + 1],
                         self.vimiv.get_pos(True))
        # h moves 1 to the left
        self.thumb.move_direction("h")
        self.assertEqual(self.vimiv.get_paths()[start],
                         self.vimiv.get_pos(True))
        # j/k/J/K do not do anything as there is only 1 row
        for direction in "jkJK":
            self.thumb.move_direction(direction)
            self.assertEqual(self.vimiv.get_paths()[start],
                             self.vimiv.get_pos(True))
        # L moves to the last element
        self.thumb.move_direction("L")
        self.assertEqual(self.vimiv.get_paths()[-1], self.vimiv.get_pos(True))
        # H moves back to the first element
        self.thumb.move_direction("H")
        self.assertEqual(self.vimiv.get_paths()[0],
                         self.vimiv.get_pos(True))
        # L and H directly from the window implementation of scroll
        self.vimiv["main_window"].scroll("L")
        self.assertEqual(self.vimiv.get_paths()[-1], self.vimiv.get_pos(True))
        self.vimiv["main_window"].scroll("H")
        self.assertEqual(self.vimiv.get_paths()[0],
                         self.vimiv.get_pos(True))

    def test_search(self):
        """Search in thumbnail mode."""
        # Incsearch
        self.vimiv["commandline"].incsearch = True
        self.vimiv["commandline"].cmd_search()
        self.vimiv["commandline"].set_text("/symlink")
        self.assertIn("symlink_to_image",
                      self.vimiv.get_paths()[self.thumb.get_position()])
        self.vimiv["commandline"].leave()
        # Normal search
        self.vimiv["commandline"].incsearch = False
        self.run_search("logo")
        self.assertIn("arch-logo", self.vimiv.get_pos(True))

    def test_zoom(self):
        """Zoom in thumbnail mode."""
        # Zoom to the value of 128
        while self.thumb.get_zoom_level()[0] > 128:
            self.thumb.zoom(False)
        while self.thumb.get_zoom_level()[0] < 128:
            self.thumb.zoom(True)
        self.assertEqual(self.thumb.get_zoom_level(), (128, 128))
        # Zoom in and check thumbnail size and pixbuf
        self.thumb.zoom(True)
        self.assertEqual(self.thumb.get_zoom_level(), (256, 256))
        # Zoom in twice should end at (512, 512)
        self.thumb.zoom(True)
        refresh_gui()
        self.thumb.zoom(True)
        self.assertEqual(self.thumb.get_zoom_level(), (512, 512))
        # We check the pixbuf here as well
        pixbuf = self._get_thumbnail_pixbuf(0)
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        scale = max(width, height)
        self.assertEqual(scale, 512)
        # Zoom out
        self.thumb.zoom(False)
        self.thumb.zoom(False)
        self.assertEqual(self.thumb.get_zoom_level(), (128, 128))
        # Zoom directly with the window implementation of zoom
        self.vimiv["window"].zoom(True)
        self.assertEqual(self.thumb.get_zoom_level(), (256, 256))
        self.vimiv["window"].zoom(False)
        self.assertEqual(self.thumb.get_zoom_level(), (128, 128))

    def _get_thumbnail_name(self):
        model = self.thumb.get_model()
        index = self.thumb.get_position()
        return model.get_value(model.get_iter(index), 1)

    def _get_thumbnail_pixbuf(self, index):
        model = self.thumb.get_model()
        return model.get_value(model.get_iter(index), 0)

    def tearDown(self):
        if self.thumb.toggled:
            self.thumb.toggle()
        self.vimiv.index = 0


if __name__ == "__main__":
    main()
