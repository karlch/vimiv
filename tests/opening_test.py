#!/usr/bin/env python
# encoding: utf-8

import os
from unittest import TestCase, main
from vimiv.fileactions import populate
import vimiv.main as v_main
from vimiv.parser import parse_config


class OpeningTest(TestCase):

    def setUp(self):
        self.settings = parse_config()

    def test_opening_without_path(self):
        vimiv = v_main.Vimiv(self.settings, [], 0)
        vimiv.main(True)

    def test_opening_with_directory(self):
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

    def test_opening_recursively(self):
        paths, index = populate([], True, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main(True)
        self.assertEqual(5, len(vimiv.paths))
        os.chdir("..")


if __name__ == '__main__':
    main()
