#!/usr/bin/env python
# encoding: utf-8
"""Test helpers.py for vimiv's test suite."""

import os
import shutil
from unittest import TestCase, main
import vimiv.helpers as helpers


class HelpersTest(TestCase):
    """Helpers Tests."""

    def setUp(self):
        os.mkdir("tmp_testdir")
        open("tmp_testdir/foo", "a").close()
        open("tmp_testdir/.foo", "a").close()

    def test_listdir_wrapper(self):
        """Check the listdir_wrapper (hidden/no_hidden)."""
        no_hidden_files = helpers.listdir_wrapper("tmp_testdir", False)
        hidden_files = helpers.listdir_wrapper("tmp_testdir", True)
        self.assertEqual(len(no_hidden_files), 1)
        self.assertEqual(len(hidden_files), 2)
        self.assertEqual(hidden_files, sorted(hidden_files))

    def test_read_file(self):
        """Check if a file is read correctly into a list of its lines."""
        helpers.read_file("tmp_testdir/bar")
        self.assertTrue(os.path.exists("tmp_testdir/bar"))
        with open("tmp_testdir/baz", "w") as created_file:
            created_file.write("vimiv\nis\ngreat")
        created_file_content = helpers.read_file("tmp_testdir/baz")
        self.assertEqual(created_file_content, ["vimiv", "is", "great"])

    def test_sizeof_fmt(self):
        """Format filesize in human-readable format."""
        readable_size = helpers.sizeof_fmt(100)
        self.assertEqual(readable_size, "100B")
        readable_size = helpers.sizeof_fmt(10240)
        self.assertEqual(readable_size, "10.0K")
        huge_size = 1024**8 * 12
        readable_size = helpers.sizeof_fmt(huge_size)
        self.assertEqual(readable_size, "12.0Y")

    def test_error_message(self):
        """Error message popup."""
        # Not much can happen here, if all attributes are set correctly it will
        # also run
        helpers.error_message("Test error", True)

    def test_read_info_from_man(self):
        """Read command information from the vimiv manpage."""
        infodict = helpers.read_info_from_man()
        # Check if some keys exist
        self.assertIn("set brightness", infodict)
        self.assertIn("center", infodict)
        # Check if the first sentence is added correctly
        # Simple
        center_info = infodict["center"]
        self.assertEqual(center_info, "Scroll to the center of the image")
        # On two lines
        autorot_info = infodict["autorotate"]
        self.assertEqual(
            autorot_info,
            "Rotate all images in the current filelist according to EXIF data")
        # Containing extra periods
        trash_info = infodict["clear_trash"]
        self.assertEqual(trash_info, "Delete all files in ~/.vimiv/Trash")
        # More than one sentence
        flip_info = infodict["flip"]
        self.assertEqual(flip_info, "Flip the image")

    def tearDown(self):
        shutil.rmtree("tmp_testdir")


if __name__ == '__main__':
    main()
