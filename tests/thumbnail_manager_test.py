# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test thumbnail_manager.py for vimiv's test suite.

Most of the base class ThumbnailManager is indirectly tested in the thumbnail
test. We therefore test the implementation of the ThumbnailStore directly.
"""

import hashlib
import os
import shutil
from tempfile import mkdtemp
from unittest import main, TestCase

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import GLib

from vimiv.thumbnail_manager import ThumbnailStore


class ThumbnailManagerTest(TestCase):
    """Test thumbnail_manager."""

    @classmethod
    def setUpClass(cls):
        cls.thumb_store = ThumbnailStore()
        cache_dir = GLib.get_user_cache_dir()
        cls.thumb_dir = os.path.join(cache_dir, "thumbnails/large")

    def test_get_thumbnail(self):
        """Get the filename of the thumbnail and create it."""
        # Standard file for which the thumbnail does not yet exist
        new_dir = mkdtemp()
        new_file = os.path.join(new_dir, "test.png")
        shutil.copyfile("vimiv/testimages/arch-logo.png", new_file)
        received_name = self.thumb_store.get_thumbnail(new_file)
        # Check name
        uri = "file://" + os.path.abspath(os.path.expanduser(new_file))
        thumb_name = hashlib.md5(bytes(uri, "utf-8")).hexdigest() + ".png"
        expected_name = os.path.join(self.thumb_dir, thumb_name)
        self.assertEqual(received_name, expected_name)
        # File should exist and is a file
        self.assertTrue(os.path.isfile(received_name))

        # Now the newly generated thumbnail file
        received_name = self.thumb_store.get_thumbnail(expected_name)
        self.assertEqual(received_name, expected_name)

        # A file that does not exist
        self.assertFalse(self.thumb_store.get_thumbnail("bla"))

        # Remove it for clean-up
        os.remove(received_name)


if __name__ == "__main__":
    main()
