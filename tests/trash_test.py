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
        cls.testfile = ""
        cls.basename = ""

    def setUp(self):
        _, self.testfile = tempfile.mkstemp()
        self.basename = os.path.basename(self.testfile)
        self._create_file()
        self.assertTrue(os.path.exists(self.testfile))

    def test_move_to_trash(self):
        """Move a file to the trash directory."""
        self.trash_manager.delete(self.testfile)
        self.assertFalse(os.path.exists(self.testfile))  # File should not exist
        # Trash file should exist and contain "something"
        expected_trashfile = os.path.join(self.files_directory, self.basename)
        self.assertTrue(os.path.exists(expected_trashfile))
        with open(expected_trashfile) as f:
            content = f.read()
            self.assertEqual(content, "something\n")
        # Info file should exist and contain path, and date
        expected_infofile = os.path.join(self.info_directory,
                                         self.basename + ".trashinfo")
        self.assertTrue(os.path.exists(expected_infofile))
        with open(expected_infofile) as f:
            lines = f.readlines()
            self.assertEqual(lines[0], "[Trash Info]\n")
            self.assertEqual(lines[1], "Path=%s\n" % (self.testfile))
            self.assertIn("DeletionDate=%s" % (time.strftime("%Y%m")), lines[2])

    def test_undelete_from_trash(self):
        """Undelete a file from trash."""
        # First delete a file
        self.trash_manager.delete(self.testfile)
        self.assertFalse(os.path.exists(self.testfile))
        # Now undelete it
        self.trash_manager.undelete(self.basename)
        self.assertTrue(os.path.exists(self.testfile))

    def test_delete_file_with_same_name(self):
        """Delete a file with the same name more than twice."""
        def run_one_round(suffix=""):
            """Tet if self.testfile + suffix exists in trash."""
            self.trash_manager.delete(self.testfile)
            self.assertFalse(os.path.exists(self.testfile))
            expected_trashfile = \
                os.path.join(self.files_directory, self.basename + suffix)
            self.assertTrue(os.path.exists(expected_trashfile))
            self._create_file()
        run_one_round()
        run_one_round(".2")
        run_one_round(".3")

    def _create_file(self):
        with open(self.testfile, "w") as f:
            f.write("something\n")

    def tearDown(self):
        if os.path.exists(self.testfile):
            os.remove(self.testfile)


if __name__ == "__main__":
    main()
