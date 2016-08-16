#!/usr/bin/env python
# encoding: utf-8
""" Tests manipulate.py for vimiv's test suite """

import os
import shutil
from unittest import TestCase, main
import vimiv.main as v_main
from vimiv.fileactions import populate
from vimiv.parser import parse_config


class ManipulateTest(TestCase):
    """ Manipulate Tests """

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        os.chdir("vimiv")
        cls.settings = parse_config()
        shutil.copytree("testimages", "testimages_man")
        paths, index = populate(["testimages_man/arch-logo.png"])
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.vimiv.main(True)
        cls.manipulate = cls.vimiv.manipulate

    def test_get_manipulated_images(self):
        """ Get images to manipulate """
        # Nothing marked -> current image
        expected_images = [self.vimiv.paths[self.vimiv.index]]
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(expected_images, received_images)
        # Marked images
        marked = ["arch-logo.png", "symlink_to_image"]
        marked = [os.path.abspath(image) for image in marked]
        self.vimiv.mark.marked = marked
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(marked, received_images)
        # Reset mark
        self.vimiv.mark.marked = []

    def test_delete(self):
        """ Delete images """
        self.assertTrue(os.path.exists("arch-logo.png"))
        self.manipulate.delete()
        self.assertFalse(os.path.exists("arch-logo.png"))
        self.assertEqual(self.vimiv.paths[self.vimiv.index],
                         os.path.abspath("arch_001.jpg"))

    def test_rotate(self):
        """ Rotate image """
        pixbuf = self.vimiv.image.image.get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.manipulate.rotate(1, False)
        pixbuf = self.vimiv.image.image.get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertTrue(is_portrait)

    def test_flip(self):
        """ Flip image """
        # simply run through the function, TODO find a way to test a flip
        self.manipulate.flip(1, False)

    def test_toggle(self):
        """ Toggle manipulate """
        self.manipulate.toggle()
        self.assertTrue(self.manipulate.toggled)
        self.assertTrue(self.manipulate.scale_bri.is_focus())
        self.manipulate.toggle()
        self.assertFalse(self.manipulate.toggled)
        self.assertFalse(self.manipulate.scale_bri.is_focus())
        self.assertTrue(self.vimiv.image.scrolled_win.is_focus())

    def test_manipulate_image(self):
        """ Test manipulate image """
        self.manipulate.toggle()
        self.manipulate.manipulate_image()
        # temporary thumbnails are created correctly
        files = os.listdir(".")
        self.assertTrue("arch_001-EDIT.jpg" in files)
        self.assertTrue("arch_001-EDIT-ORIG.jpg" in files)
        self.assertTrue(
            "arch_001-EDIT.jpg" in self.vimiv.paths[self.vimiv.index])
        self.manipulate.button_clicked(None, False)
        self.manipulate.toggle()
        self.manipulate.manipulations = [20, 20, 20, False]
        self.manipulate.button_clicked(None, True)

    def test_manipulate_sliders(self):
        """ Focusing and changing values of sliders """
        self.manipulate.toggle()
        self.manipulate.focus_slider("bri")
        self.manipulate.change_slider(True, False)
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
        """ Test manipulating from command line commands """
        self.manipulate.cmd_edit("sha", 20)
        self.assertEqual(self.manipulate.scale_sha.get_value(), 20)
        self.assertTrue(self.manipulate.scale_sha.is_focus())
        self.manipulate.button_clicked(None, False)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.working_directory)
        if os.path.isdir("./vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")


if __name__ == "__main__":
    main()
