#!/usr/bin/env python
# encoding: utf-8

from unittest import main
from vimiv_testcase import VimivTestCase


class ImageTest(VimivTestCase):
    """Image mode Test."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch_001.jpg"])
        cls.image = cls.vimiv["image"]

    def test_zoom_percent(self):
        """Test getting the fitting image zoom."""
        # Panorama image
        width = 1920
        im_width = self.image.imsize[0]
        perc = self.image.get_zoom_percent_to_fit()
        self.assertEqual(im_width/width, perc)

    def test_zooming(self):
        """Zooming of images."""
        width = 1920
        # Zoom in by 30 %
        perc_before = self.image.zoom_percent
        self.image.zoom_delta(0.3)
        self.assertEqual(self.image.zoom_percent, perc_before * 1.3)
        # Zoom to a size representing half the image size
        self.image.zoom_to(0.5)
        self.assertEqual(self.image.zoom_percent, 0.5)
        pixbuf = self.image.image.get_pixbuf()
        self.assertEqual(width * 0.5, pixbuf.get_width())
        # Zoom by keyhandler
        self.vimiv["keyhandler"].num_str = "03"
        self.image.zoom_to(0)
        self.assertEqual(self.image.zoom_percent, 1/3)
        pixbuf = self.image.image.get_pixbuf()
        self.assertEqual(width * (1/3), pixbuf.get_width())
        # Zoom back to fit
        self.image.zoom_to(0)
        self.assertEqual(self.image.zoom_percent,
                self.image.get_zoom_percent_to_fit())
        pixbuf = self.image.image.get_pixbuf()
        self.assertEqual(width * self.image.get_zoom_percent_to_fit(),
                         pixbuf.get_width())
        # Unreasonable zoom
        self.image.zoom_to(1000)
        message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(message, "Warning: Object cannot be zoomed (further)")
        pixbuf = self.image.image.get_pixbuf()
        self.assertEqual(width * self.image.get_zoom_percent_to_fit(),
                         pixbuf.get_width())
        # Non parseable percentage
        self.vimiv["keyhandler"].num_str = "vimiv"
        self.image.zoom_to(0)
        message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(message, "Error: Zoom percentage not parseable")

    def test_move(self):
        """Move from image to image."""
        self.assertEqual(0, self.vimiv.index)
        self.image.move_index()
        self.assertEqual(1, self.vimiv.index)
        self.image.move_index(forward=False)
        self.assertEqual(0, self.vimiv.index)
        self.image.move_index(delta=2)
        self.assertEqual(2, self.vimiv.index)
        self.image.move_pos()
        self.assertEqual(len(self.vimiv.paths) - 1, self.vimiv.index)
        self.image.move_pos(forward=False)
        self.assertEqual(0, self.vimiv.index)

    def test_toggles(self):
        """Toggle image.py settings."""
        # Rescale svg
        before = self.image.rescale_svg
        self.image.toggle_rescale_svg()
        self.assertFalse(before == self.image.rescale_svg)
        self.image.toggle_rescale_svg()
        self.assertTrue(before == self.image.rescale_svg)
        # Overzoom
        before = self.image.overzoom
        self.image.toggle_overzoom()
        self.assertFalse(before == self.image.overzoom)
        self.image.toggle_overzoom()
        self.assertTrue(before == self.image.overzoom)
        # Animations should be tested in animation_test.py

    def test_check_for_edit(self):
        """Check if an image was edited."""
        path = self.vimiv.paths[self.vimiv.index]
        self.assertEqual(0, self.image.check_for_edit(False))
        self.vimiv.paths[self.vimiv.index] = "some-EDIT.jpg"
        self.assertEqual(1, self.image.check_for_edit(False))
        self.assertEqual(0, self.image.check_for_edit(True))
        # Reset path
        self.vimiv.paths[self.vimiv.index] = path

if __name__ == '__main__':
    main()
