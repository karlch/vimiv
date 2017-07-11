# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test imageactions.py for vimiv's test suite."""

import os
import shutil
import time
from unittest import TestCase, main

from gi import require_version
require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

import vimiv.imageactions as imageactions

from vimiv_testcase import compare_files


class ImageActionsTest(TestCase):
    """Imageactions Tests."""

    def setUp(self):
        self.working_directory = os.getcwd()
        os.chdir("vimiv/testimages/")
        self.orig = os.path.abspath("arch_001.jpg")
        self.filename = os.path.abspath("image_to_edit.jpg")
        self.filename_2 = os.path.abspath("image_to_edit_2.jpg")
        self._waiting = False  # Used to wait for autorotate
        shutil.copyfile(self.orig, self.filename)
        shutil.copyfile(self.orig, self.filename_2)

    def test_rotate(self):
        """Rotate image file."""
        def do_rotate_test(rotate_int):
            """Run the rotation test.

            Args:
                rotate_int: Number defining the rotation.
            """
            pb = GdkPixbuf.Pixbuf.new_from_file(self.filename)
            orientation_before = pb.get_width() < pb.get_height()
            imageactions.rotate_file(self.filename, rotate_int)
            pb = GdkPixbuf.Pixbuf.new_from_file(self.filename)
            orientation_after = pb.get_width() < pb.get_height()
            if rotate_int in [1, 3]:
                self.assertNotEqual(orientation_before, orientation_after)
            elif rotate_int == 2:
                self.assertEqual(orientation_before, orientation_after)
        # Rotate counterclockwise
        do_rotate_test(1)
        # Rotate clockwise
        do_rotate_test(3)
        # Images are now equal again
        self.assertTrue(compare_files(self.orig, self.filename))
        # Rotate 180
        do_rotate_test(2)
        # Images are not equal
        self.assertFalse(compare_files(self.orig, self.filename))

    def test_flip(self):
        """Flipping of files."""
        # Images equal before the flip
        self.assertTrue(compare_files(self.orig, self.filename))
        # Images differ after the flip
        imageactions.flip_file(self.filename, False)
        self.assertFalse(compare_files(self.orig, self.filename))
        # Images equal after flipping again
        imageactions.flip_file(self.filename, False)
        self.assertTrue(compare_files(self.orig, self.filename))
        # Same for horizontal flip
        # Images equal before the flip
        self.assertTrue(compare_files(self.orig, self.filename))
        # Images differ after the flip
        imageactions.flip_file(self.filename, True)
        self.assertFalse(compare_files(self.orig, self.filename))
        # Images equal after flipping again
        imageactions.flip_file(self.filename, True)
        self.assertTrue(compare_files(self.orig, self.filename))

    def test_autorotate(self):
        """Autorotate files."""
        pb = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        orientation_before = pb.get_width() < pb.get_height()
        autorotate = imageactions.Autorotate([self.filename])
        autorotate.connect("completed", self._on_autorotate_completed)
        autorotate.run()
        # Wait for it to complete
        self._waiting = True
        while self._waiting:
            time.sleep(0.05)
        pb = GdkPixbuf.Pixbuf.new_from_file(self.filename)
        orientation_after = pb.get_width() < pb.get_height()
        self.assertNotEqual(orientation_before, orientation_after)

    def _on_autorotate_completed(self, autorotate, amount):
        self._waiting = False

    def tearDown(self):
        os.chdir(self.working_directory)
        os.remove(self.filename)
        os.remove(self.filename_2)


if __name__ == "__main__":
    main()
