# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test imageactions.py for vimiv's test suite."""

import os
import shutil
from tempfile import mkdtemp
from unittest import TestCase, main

import vimiv.imageactions as imageactions
from PIL import Image

from vimiv_testcase import compare_images


class ImageActionsTest(TestCase):
    """Imageactions Tests."""

    def setUp(self):
        self.working_directory = os.getcwd()
        os.chdir("vimiv/testimages/")
        self.orig = os.path.abspath("arch_001.jpg")
        self.filename = os.path.abspath("image_to_edit.jpg")
        self.filename_2 = os.path.abspath("image_to_edit_2.jpg")
        shutil.copyfile(self.orig, self.filename)
        shutil.copyfile(self.orig, self.filename_2)
        self.files = [self.filename]
        self.thumbdir = mkdtemp()

    def test_rotate(self):
        """Rotate image file."""
        def do_rotate_test(rotate_int):
            """Run the rotation test.

            Args:
                rotate_int: Number defining the rotation.
            """
            with Image.open(self.filename) as im:
                orientation_before = im.size[0] < im.size[1]
            imageactions.rotate_file(self.files, rotate_int)
            with Image.open(self.filename) as im:
                orientation_after = im.size[0] < im.size[1]
            if rotate_int in [1, 3]:
                self.assertNotEqual(orientation_before, orientation_after)
            elif rotate_int == 2:
                self.assertEqual(orientation_before, orientation_after)
        # Rotate counterclockwise
        do_rotate_test(1)
        # Rotate clockwise
        do_rotate_test(3)
        # Images are now equal again
        self.assertTrue(compare_images(self.orig, self.filename))
        # Rotate 180
        do_rotate_test(2)
        # Images are not equal
        self.assertFalse(compare_images(self.orig, self.filename))

    def test_flip(self):
        """Flipping of files."""
        # Images equal before the flip
        self.assertTrue(compare_images(self.orig, self.filename))
        # Images differ after the flip
        imageactions.flip_file(self.files, False)
        self.assertFalse(compare_images(self.orig, self.filename))
        # Images equal after flipping again
        imageactions.flip_file(self.files, False)
        self.assertTrue(compare_images(self.orig, self.filename))
        # Same for horizontal flip
        # Images equal before the flip
        self.assertTrue(compare_images(self.orig, self.filename))
        # Images differ after the flip
        imageactions.flip_file(self.files, True)
        self.assertFalse(compare_images(self.orig, self.filename))
        # Images equal after flipping again
        imageactions.flip_file(self.files, True)
        self.assertTrue(compare_images(self.orig, self.filename))

    def test_thumbnails_create(self):
        """Creation of thumbnail files."""
        expected_name = \
            self.files[0].replace("/", "___").lstrip("___") + \
            ".thumbnail_128x128.png"
        thumbnails = imageactions.Thumbnails(self.files, (128, 128),
                                             self.thumbdir)
        thumbnails.thumbnails_create()
        # Check if thumbnail exists
        thumbnail = os.path.join(self.thumbdir, expected_name)
        self.assertTrue(os.path.isfile(thumbnail))
        # Check its size
        with Image.open(thumbnail) as im:
            thumbnail_size = max(im.size[0], im.size[1])
            self.assertEqual(thumbnail_size, 128)

    def test_autorotate(self):
        """Autorotate files."""
        # Method jhead
        if not shutil.which("jhead"):
            self.fail("jhead is not installed.")
        n_rotated, method = imageactions.autorotate(self.files)
        self.assertEqual(method, "jhead")
        self.assertEqual(n_rotated, 1)
        # Method PIL
        n_rotated, method = imageactions.autorotate([self.filename_2], "PIL")
        self.assertEqual(method, "PIL")
        self.assertEqual(n_rotated, 1)

    def tearDown(self):
        os.chdir(self.working_directory)
        os.remove(self.filename)
        os.remove(self.filename_2)
        shutil.rmtree(self.thumbdir)


if __name__ == "__main__":
    main()
