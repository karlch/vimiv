# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test vimiv's trash management."""

import os
import tempfile
import time

from unittest import TestCase, main

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import GLib

from vimiv import trash_manager


class TrashTest(TestCase):
    """TrashManager Tests."""

    @classmethod
    def setUpClass(cls):
        # Run in tmp
        cls.tmpdir = tempfile.TemporaryDirectory(prefix="vimiv-tests-")
        os.environ["XDG_DATA_HOME"] = cls.tmpdir.name
        cls.trash_manager = trash_manager.TrashManager()
        cls.files_directory = os.path.join(GLib.get_user_data_dir(),
                                           "Trash/files")
        cls.info_directory = os.path.join(GLib.get_user_data_dir(),
                                          "Trash/info")

    def test_move_to_trash(self):
        """Move a file to the trash directory."""
        _, testfile = tempfile.mkstemp()
        basename = os.path.basename(testfile)
        with open(testfile, "w") as f:
            f.write("something")
        self.trash_manager.delete(testfile)
        self.assertFalse(os.path.exists(testfile))  # File should not exist
        # Trash file should exist and contain "something"
        expected_trashfile = os.path.join(self.files_directory, basename)
        self.assertTrue(os.path.exists(expected_trashfile))
        with open(expected_trashfile) as f:
            content = f.read()
            self.assertEqual(content, "something")
        # Info file should exist and contain path, and date
        expected_infofile = os.path.join(self.info_directory,
                                         basename + ".trashinfo")
        self.assertTrue(os.path.exists(expected_infofile))
        with open(expected_infofile) as f:
            lines = f.readlines()
            self.assertEqual(lines[0], "[Trash Info]\n")
            self.assertEqual(lines[1], "Path=%s\n" % (testfile))
            self.assertIn("DeletionDate=%s" % (time.strftime("%Y%m")), lines[2])

    def test_undelete_from_trash(self):
        """Undelete a file from trash."""
        # First delete a file
        _, testfile = tempfile.mkstemp()
        basename = os.path.basename(testfile)
        with open(testfile, "w") as f:
            f.write("something")
        self.trash_manager.delete(testfile)
        self.assertFalse(os.path.exists(testfile))
        # Now undelete it
        self.trash_manager.undelete(basename)
        self.assertTrue(os.path.exists(testfile))


if __name__ == "__main__":
    main()
