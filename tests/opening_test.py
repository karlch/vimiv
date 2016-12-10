#!/usr/bin/env python
# encoding: utf-8
"""Test the opening of different file-types with vimiv."""

import os
from unittest import main
from vimiv_testcase import VimivTestCase


class OpeningTest(VimivTestCase):
    """Open with different file-types Test."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def test_opening_with_directory(self):
        """Opening with a directory."""
        expected_dir = os.path.abspath("vimiv/testimages")
        self.init_test(["vimiv/testimages"])
        self.assertEqual(expected_dir, os.getcwd())
        expected_files = ["animation", "arch-logo.png", "arch_001.jpg",
                          "directory", "symlink_to_image", "vimiv.bmp",
                          "vimiv.svg", "vimiv.tiff"]
        self.assertEqual(self.vimiv["library"].files, expected_files)
        self.assertTrue(self.vimiv["library"].treeview.is_focus())
        self.assertTrue(self.vimiv["library"].grid.is_visible())

    def test_opening_with_image(self):
        """Open with an image."""
        expected_dir = os.path.abspath("vimiv/testimages")
        self.init_test(["vimiv/testimages/arch_001.jpg"])
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["arch_001.jpg", "symlink_to_image", "vimiv.bmp",
                           "vimiv.svg", "vimiv.tiff", "arch-logo.png"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, self.vimiv.paths)

    def test_opening_with_symlink(self):
        """Open with a symlink to an image."""
        expected_dir = os.path.abspath("vimiv/testimages")
        self.init_test(["vimiv/testimages/symlink_to_image"])
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink_to_image", "vimiv.bmp", "vimiv.svg",
                           "vimiv.tiff", "arch-logo.png", "arch_001.jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, self.vimiv.paths)

    def test_opening_with_whitespace(self):
        """Open an image with whitespace and symlink in directory."""
        expected_dir = os.path.abspath("vimiv/testimages/directory/")
        self.init_test(["vimiv/testimages/directory/symlink with spaces .jpg"])
        # Check moving and image population
        self.assertEqual(expected_dir, os.getcwd())
        expected_images = ["symlink with spaces .jpg"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(expected_images, self.vimiv.paths)

    def test_opening_recursively(self):
        """Open all images recursively."""
        # Need to backup because we init in the wrong directory here
        working_dir = self.working_directory
        os.chdir("vimiv/testimages")
        self.init_test(["."], ["GENERAL"], ["recursive"], [True])
        self.assertEqual(8, len(self.vimiv.paths))
        self.working_directory = working_dir

    def tearDown(self):
        os.chdir(self.working_directory)
        self.vimiv.quit()


if __name__ == '__main__':
    main()
