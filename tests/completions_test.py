# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Completion tests for vimiv's test suite."""

import os
import shutil
from unittest import main

from vimiv.trash_manager import TrashManager

from vimiv_testcase import VimivTestCase


class CompletionsTest(VimivTestCase):
    """Completions Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.completions = cls.vimiv["completions"]

    def test_reset(self):
        """Reset the internal completion values."""
        self.completions.tab_presses = 42
        self.completions.tab_position = 42
        self.completions.reset()
        self.assertEqual(self.completions.tab_presses, 0)
        self.assertEqual(self.completions.tab_position, 0)

    def test_internal_completion(self):
        """Completion of internal commands."""
        self.completions.entry.set_text(":a")
        self.completions.complete()
        expected_completions = ["accept_changes", "alias", "autorotate"]
        liststore = self.completions.treeview.get_model()
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))
        # Internal completion with a prefixed digit
        self.completions.entry.set_text(":5a")
        self.completions.complete()
        expected_completions = ["accept_changes", "alias", "autorotate"]
        liststore = self.completions.treeview.get_model()
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))

    def test_external_completion(self):
        """Completion of external commands. Currently none."""
        self.completions.entry.set_text(":!vimi")
        self.completions.complete()
        liststore = self.completions.treeview.get_model()
        self.assertFalse(len(liststore))

    def test_external_path_completion(self):
        """Completion of paths for external commands."""
        # One path
        self.completions.entry.set_text(":!mv vi")
        expected_completions = ["!mv vimiv/"]
        liststore = self.completions.treeview.get_model()
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))
        # Two paths
        self.completions.entry.set_text(":!mv % vi")
        expected_completions = ["!mv % vimiv/"]
        liststore = self.completions.treeview.get_model()
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))
        # Do not complete arguments
        self.completions.entry.set_text(":!mv -")
        self.completions.complete()
        liststore = self.completions.treeview.get_model()
        self.assertFalse(len(liststore))

    def test_path_completion(self):
        """Completion of paths."""
        self.completions.entry.set_text(":./vimiv/testimages/ar")
        self.completions.complete()
        expected_completions = ["./vimiv/testimages/arch-logo.png",
                                "./vimiv/testimages/arch_001.jpg"]
        liststore = self.completions.treeview.get_model()
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))
        # Expand home
        self.vimiv["library"].show_hidden = True
        self.completions.entry.set_text(":~/.loca")
        liststore = self.completions.treeview.get_model()
        completions = []
        for row in liststore:
            completions.append(row[0])
        self.assertIn("~/.local/", completions)
        self.vimiv["library"].show_hidden = False

    def test_tag_completion(self):
        """Completion of tags."""
        # Create one tag
        new_tagfile = os.path.join(self.vimiv["tags"].directory, "testfile")
        with open(new_tagfile, "w") as f:
            f.write(os.path.abspath("vimiv/testimages/arch-logo.png"))
        tagfiles = os.listdir(self.vimiv["tags"].directory)
        self.completions.entry.set_text(":tag_load ")
        self.completions.complete()
        liststore = self.completions.treeview.get_model()
        expected_completions = ["tag_load " + tag for tag in tagfiles]
        for row in liststore:
            self.assertIn(row[0], expected_completions)
        self.assertEqual(len(liststore), len(expected_completions))

    def test_trash_completion(self):
        """Completion of files in trash."""
        # Create one image file in trash and one with a similar name but not an
        # image
        # The completion is supposed to be unique as the non-image is ignored
        trash_directory = TrashManager().get_files_directory()
        trashed_file = os.path.join(trash_directory, "arch-logo.png")
        shutil.copy("vimiv/testimages/arch-logo.png", trash_directory)
        with open(os.path.join(trash_directory, "arch-logo.txt"), "w") as f:
            f.write("test\n")
        self.completions.entry.set_text(":undelete ")
        self.completions.complete()
        expected_text = ":undelete arch-logo.png"
        self.assertEqual(expected_text, self.completions.entry.get_text())
        # Clean up
        os.remove(trashed_file)

    def test_tabbing(self):
        """Tabbing through completions."""
        # Complete to last matching character
        self.completions.entry.set_text(":co")
        self.completions.complete()
        expected_text = ":copy_"
        received_text = self.completions.entry.get_text()
        self.assertEqual(expected_text, received_text)
        # First result
        liststore = self.completions.treeview.get_model()
        self.vimiv["completions"].complete()
        expected_text = "copy_abspath"
        selected_path = self.completions.treeview.get_cursor()[0]
        selected_index = selected_path.get_indices()[0]
        selected_text = liststore[selected_index][0]
        self.assertEqual(expected_text, selected_text)
        # Second result
        self.vimiv["completions"].complete()
        expected_text = "copy_basename"
        selected_path = self.completions.treeview.get_cursor()[0]
        selected_index = selected_path.get_indices()[0]
        selected_text = liststore[selected_index][0]
        self.assertEqual(expected_text, selected_text)
        # First again
        self.vimiv["completions"].complete(inverse=True)
        expected_text = "copy_abspath"
        selected_path = self.completions.treeview.get_cursor()[0]
        selected_index = selected_path.get_indices()[0]
        selected_text = liststore[selected_index][0]
        self.assertEqual(expected_text, selected_text)
        # Now activate the completion
        self.completions.activate(None, None, None)
        entry_text = self.completions.entry.get_text()
        expected_text = ":copy_abspath"
        self.assertEqual(expected_text, entry_text)

    def test_best_match_with_prefix(self):
        """Complete to best match with a prefixed number."""
        # Complete to last matching character
        self.completions.entry.set_text(":2co")
        self.completions.complete()
        expected_text = ":2copy_"
        received_text = self.completions.entry.get_text()
        self.assertEqual(expected_text, received_text)

    def test_selections(self):
        """Initial selection when tabbing through completions."""
        self.vimiv["commandline"].focus()
        # No cursor yet
        cursor = self.completions.treeview.get_cursor()[0]
        self.assertIsNone(cursor)
        # Tab should start at index 0
        self.completions.complete()
        cursor = self.completions.treeview.get_cursor()[0]
        self.assertIsNotNone(cursor)
        index = cursor.get_indices()[0]
        self.assertEqual(index, 0)
        # Re-open the completion
        self.completions.hide()
        self.completions.reset()
        self.completions.entry.set_text(":")
        self.completions.show()
        # No cursor again
        cursor = self.completions.treeview.get_cursor()[0]
        self.assertIsNone(cursor)
        # Inverse Tab should start at index -1
        self.completions.complete(True)
        cursor = self.completions.treeview.get_cursor()[0]
        self.assertIsNotNone(cursor)
        index = cursor.get_indices()[0]
        last = len(self.completions.treeview.get_model()) - 1
        self.assertEqual(index, last)


if __name__ == "__main__":
    main()
