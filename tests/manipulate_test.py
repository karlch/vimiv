#!/usr/bin/env python
# encoding: utf-8
"""Test manipulate.py for vimiv's test suite."""

import os
import shutil
from unittest import main
from vimiv_testcase import VimivTestCase, compare_images


class ManipulateTest(VimivTestCase):
    """Manipulate Tests."""

    @classmethod
    def setUpClass(cls):
        shutil.copytree("vimiv/testimages", "vimiv/testimages_man")
        cls.init_test(cls, ["vimiv/testimages_man/arch-logo.png"])
        cls.manipulate = cls.vimiv["manipulate"]

    def test_get_manipulated_images(self):
        """Get images to manipulate."""
        # Nothing marked -> current image
        expected_images = [self.vimiv.paths[self.vimiv.index]]
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(expected_images, received_images)
        # Marked images
        marked = ["arch-logo.png", "symlink_to_image"]
        marked = [os.path.abspath(image) for image in marked]
        self.vimiv["mark"].marked = marked
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(marked, received_images)
        # Reset mark
        self.vimiv["mark"].marked = []

    def test_delete(self):
        """Delete images."""
        self.assertTrue(os.path.exists("arch-logo.png"))
        self.manipulate.delete()
        self.assertFalse(os.path.exists("arch-logo.png"))
        self.assertEqual(self.vimiv.paths[self.vimiv.index],
                         os.path.abspath("arch_001.jpg"))

    def test_rotate(self):
        """Rotate image."""
        pixbuf = self.vimiv["image"].image.get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.manipulate.rotate(1, False)
        pixbuf = self.vimiv["image"].image.get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertTrue(is_portrait)

    def test_flip(self):
        """Flip image."""
        pixbuf_before = self.vimiv["image"].image.get_pixbuf()
        self.manipulate.flip(1, False)
        pixbuf_after = self.vimiv["image"].image.get_pixbuf()
        self.assertNotEqual(pixbuf_before, pixbuf_after)

    def test_toggle(self):
        """Toggle manipulate."""
        # Via function
        self.manipulate.toggle()
        self.assertTrue(self.manipulate.scrolled_win.is_visible())
        self.assertTrue(self.manipulate.scale_bri.is_focus())
        self.manipulate.toggle()
        self.assertFalse(self.manipulate.scrolled_win.is_visible())
        self.assertFalse(self.manipulate.scale_bri.is_focus())
        self.assertTrue(self.vimiv["image"].scrolled_win.is_focus())
        # Close via button
        self.manipulate.toggle()
        self.manipulate.button_clicked(None, False)
        self.assertFalse(self.manipulate.scale_bri.is_focus())
        self.assertTrue(self.vimiv["image"].scrolled_win.is_focus())

    def test_manipulate_image(self):
        """Test manipulate image."""
        # Manipulated image is equal to old file before manipulation
        cur_image = os.path.basename(self.vimiv.paths[self.vimiv.index])
        self.assertTrue(compare_images("../testimages/" + cur_image, cur_image))
        self.manipulate.toggle()
        self.manipulate.manipulations = {"bri": 20, "con": 20, "sha": 20}
        self.manipulate.button_clicked(None, True)
        # Different afterwards
        self.assertFalse(compare_images("../testimages/" + cur_image,
                                        cur_image))

    def test_manipulate_sliders(self):
        """Focusing and changing values of sliders."""
        self.manipulate.toggle()
        self.manipulate.focus_slider("bri")
        self.manipulate.change_slider(-1)
        received_value = self.manipulate.scale_bri.get_value()
        self.assertEqual(received_value, -1)
        self.manipulate.focus_slider("con")
        self.assertTrue(self.manipulate.scale_con.is_focus())
        self.manipulate.focus_slider("sha")
        self.assertTrue(self.manipulate.scale_sha.is_focus())
        self.manipulate.focus_slider("bri")
        self.assertTrue(self.manipulate.scale_bri.is_focus())
        self.manipulate.button_clicked(None, False)

    def test_cmd_edit(self):
        """Test manipulating from command line commands."""
        self.manipulate.cmd_edit("sha", 20)
        self.assertEqual(self.manipulate.scale_sha.get_value(), 20)
        self.assertTrue(self.manipulate.scale_sha.is_focus())
        self.manipulate.button_clicked(None, False)

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)
        if os.path.isdir("./vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")


if __name__ == "__main__":
    main()
