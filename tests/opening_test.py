#!/usr/bin/env python
# encoding: utf-8
""" Tests the opening of different filetypes with vimiv """

import os
from unittest import TestCase, main
from vimiv.fileactions import populate
import vimiv.main as v_main
from vimiv.parser import parse_config


class OpeningTest(TestCase):
    """ Opening of different filetypes Test"""

    def setUp(self):
        self.settings = parse_config()

    def test_opening_without_path(self):
        """ Opening without an argument """
        vimiv = v_main.Vimiv(self.settings, [], 0)
        self.assertEqual(vimiv.paths, [])
        vimiv.main(True)

    def test_opening_with_directory(self):
        """ Opening with a directory """
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        self.assertEqual(expected_dir, os.getcwd())
        expected_files = ["arch_001.jpg", "arch-logo.png", "directory",
                          "symlink_to_image"]
        self.assertEqual(vimiv.library.files, expected_files)
        self.assertTrue(vimiv.library.focused)
        self.assertTrue(vimiv.library.toggled)
        os.chdir("..")

    def test_opening_with_image(self):
        """ Opening with an image """
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages/arch_001.jpg"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["arch_001.jpg", "symlink_to_image", "arch-logo.png"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)
        os.chdir("..")

    def test_opening_with_symlink(self):
        """ Opening with a symlink to an image """
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages/symlink_to_image"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink_to_image", "arch-logo.png", "arch_001.jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)
        os.chdir("..")

    def test_opening_with_whitespace(self):
        """ Open an image with whitespace and symlink in directory """
        expected_dir = os.path.abspath("./testimages/directory/")
        paths, index = \
                populate(["testimages/directory/symlink with spaces .jpg"],
                         False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink with spaces .jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)
        os.chdir("../..")

    def test_opening_recursively(self):
        """ Open all images recursively """
        paths, index = populate([], True, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        self.assertEqual(6, len(vimiv.paths))
        os.chdir("..")



if __name__ == '__main__':
    main()
