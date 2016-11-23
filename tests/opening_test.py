#!/usr/bin/env python
# encoding: utf-8
"""Test the opening of different file-types with vimiv."""

import os
from unittest import TestCase, main
from vimiv.fileactions import populate
import vimiv.main as v_main
from vimiv.parser import parse_config


class OpeningTest(TestCase):
    """Open with different file-types Test."""

    def setUp(self):
        self.working_directory = os.getcwd()
        os.chdir("vimiv")
        self.settings = parse_config()

    def test_opening_without_path(self):
        """Opening without an argument."""
        vimiv = v_main.Vimiv(self.settings, [], 0)
        self.assertEqual(vimiv.paths, [])
        vimiv.main()

    def test_opening_with_directory(self):
        """Opening with a directory."""
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main()
        self.assertEqual(expected_dir, os.getcwd())
        expected_files = ["animation", "arch-logo.png", "arch_001.jpg",
                          "directory", "symlink_to_image", "vimiv.bmp",
                          "vimiv.svg", "vimiv.tiff"]
        self.assertEqual(vimiv.library.files, expected_files)
        self.assertTrue(vimiv.library.treeview.is_focus())
        self.assertTrue(vimiv.library.grid.is_visible())

    def test_opening_with_image(self):
        """Open with an image."""
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages/arch_001.jpg"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main()
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["arch_001.jpg", "symlink_to_image", "vimiv.bmp",
                           "vimiv.svg", "vimiv.tiff", "arch-logo.png"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)

    def test_opening_with_symlink(self):
        """Open with a symlink to an image."""
        expected_dir = os.path.abspath("./testimages")
        paths, index = populate(["testimages/symlink_to_image"], False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main()
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink_to_image", "vimiv.bmp", "vimiv.svg",
                           "vimiv.tiff", "arch-logo.png", "arch_001.jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)

    def test_opening_with_whitespace(self):
        """Open an image with whitespace and symlink in directory."""
        expected_dir = os.path.abspath("./testimages/directory/")
        paths, index = \
            populate(["testimages/directory/symlink with spaces .jpg"],
                     False, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main()
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink with spaces .jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, vimiv.paths)

    def test_opening_recursively(self):
        """Open all images recursively."""
        os.chdir("testimages")
        paths, index = populate([], True, False)
        vimiv = v_main.Vimiv(self.settings, paths, index)
        vimiv.main()
        self.assertEqual(8, len(vimiv.paths))

    def tearDown(self):
        os.chdir(self.working_directory)


if __name__ == '__main__':
    main()
