#!/usr/bin/env python
# encoding: utf-8
"""Command line tests for vimiv's test suite."""

import os
from unittest import main
from vimiv_testcase import VimivTestCase, refresh_gui


class CommandlineTest(VimivTestCase):
    """Command Line Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def setUp(self):
        self.working_directory = os.getcwd()

    def test_toggling(self):
        """Open and leave the commandline."""
        # Focusing
        self.vimiv["commandline"].focus()
        self.assertEqual(self.vimiv["commandline"].entry.get_text(), ":")
        self.assertTrue(self.vimiv["commandline"].entry.is_focus())
        self.assertTrue(self.vimiv["commandline"].entry.is_visible())
        # Leaving by deleting the colon
        self.vimiv["commandline"].entry.set_text("")
        self.assertFalse(self.vimiv["commandline"].entry.is_visible())
        self.assertFalse(self.vimiv["commandline"].entry.is_focus())
        # Focusing with text
        self.vimiv["commandline"].focus("test")
        self.assertEqual(self.vimiv["commandline"].entry.get_text(), ":test")
        self.assertTrue(self.vimiv["commandline"].entry.is_focus())
        self.assertTrue(self.vimiv["commandline"].entry.is_visible())
        # Leaving normally
        self.vimiv["commandline"].leave()
        self.assertFalse(self.vimiv["commandline"].entry.is_visible())
        self.assertFalse(self.vimiv["commandline"].entry.is_focus())

    def test_run_command(self):
        """Run an internal vimiv command."""
        before_command = self.vimiv["image"].overzoom
        self.vimiv["commandline"].entry.set_text(":set overzoom!")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)

    def test_run_alias(self):
        """Run an alias."""
        self.vimiv.aliases = {"test_alias": "set overzoom!"}
        before_command = self.vimiv["image"].overzoom
        self.vimiv["commandline"].entry.set_text(":test_alias")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)
        # Alias that does not exist
        self.vimiv.aliases = {"test_alias": "useless_command"}
        self.vimiv["commandline"].entry.set_text(":test_alias")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        error_message = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(error_message,
                         "ERROR: No command called useless_command")

    def test_run_external(self):
        """Run an external command and test failures."""
        # Run command
        self.vimiv["commandline"].entry.set_text(":!touch tmp_foo")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        files = os.listdir()
        self.assertTrue("tmp_foo" in files)
        os.remove("tmp_foo")
        # Try to run a non-existent command
        self.vimiv["commandline"].entry.set_text(":!foo_bar_baz")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        statusbar_text = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(statusbar_text,
                         "ERROR: /bin/sh: foo_bar_baz: command not found")

    def test_pipe(self):
        """Pipe a command to vimiv."""
        # Internal command
        before_command = self.vimiv["image"].overzoom
        self.vimiv["commandline"].entry.set_text(":!echo set overzoom! |")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        refresh_gui(0.001)
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)
        # Directory
        expected_dir = os.path.abspath("./vimiv/testimages/")
        self.vimiv["commandline"].entry.set_text(":!echo vimiv/testimages |")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        refresh_gui(0.001)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Image
        expected_image = os.path.abspath("arch-logo.png")
        self.vimiv["commandline"].entry.set_text(":!echo arch-logo.png |")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        refresh_gui()
        self.assertEqual(self.vimiv.paths[0], expected_image)

    def test_path(self):
        """Enter a path in the commandline."""
        # Pass a directory
        expected_dir = os.path.abspath("./vimiv/testimages")
        self.vimiv["commandline"].entry.set_text(":./vimiv/testimages")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Pass an image
        expected_image = os.path.abspath("arch-logo.png")
        self.vimiv["commandline"].entry.set_text(":./arch-logo.png")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.assertEqual(self.vimiv.paths[0], expected_image)

    def test_search(self):
        """Search for images, directories and navigate search results."""
        self.vimiv["commandline"].cmd_search()
        self.assertEqual(self.vimiv["commandline"].entry.get_text(), "/")
        # Search should move into testimages
        expected_dir = os.path.abspath("./vimiv")
        self.vimiv["commandline"].entry.set_text("/vimi")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        expected_dir = os.path.abspath("./testimages")
        self.vimiv["commandline"].entry.set_text("/test")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Search should have these results
        self.vimiv["commandline"].search_case = False
        self.vimiv["commandline"].entry.set_text("/Ar")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        expected_search_results = [1, 2]
        search_results = self.vimiv["commandline"].search_positions
        self.assertEqual(search_results, expected_search_results)
        # Moving forward to next result should work
        self.assertEqual(self.vimiv.get_pos(), 1)
        self.vimiv["commandline"].search_move(1)
        self.assertEqual(self.vimiv.get_pos(), 2)
        # Searching case sensitively should have no results here
        self.vimiv["commandline"].search_case = True
        self.vimiv["commandline"].entry.set_text("/Ar")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.assertFalse(self.vimiv["commandline"].search_positions)

    def test_incsearch(self):
        """Incsearch."""
        dir_before = os.getcwd()
        self.vimiv["commandline"].cmd_search()
        self.assertEqual(self.vimiv["commandline"].entry.get_text(), "/")
        # Search should be done automatically
        self.vimiv["commandline"].entry.set_text("/vi")
        expected_pos = self.vimiv["library"].files.index("vimiv")
        self.assertEqual(self.vimiv["commandline"].search_positions,
                         [expected_pos])
        focused_path = self.vimiv["library"].treeview.get_cursor()[0]
        position = focused_path.get_indices()[0]
        focused_file = self.vimiv["library"].files[position]
        self.assertEqual(focused_file, "vimiv")
        # Not accepted -> Back to the default position
        self.vimiv["commandline"].leave()
        self.assertEqual(os.getcwd(), dir_before)

    def test_alias(self):
        """Add an alias."""
        self.vimiv["commandline"].alias("testalias")
        self.assertTrue("testalias" in self.vimiv.aliases)

    def test_history_search(self):
        """Search through history."""
        # First run some very fast commands
        self.vimiv["commandline"].entry.set_text(":!ls")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        self.vimiv["commandline"].entry.set_text(":!echo foo_bar")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        self.vimiv["commandline"].entry.set_text(":!echo baz")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.vimiv["commandline"].running_threads[0].join()
        # Check if they were added to the history correctly
        self.assertIn(":!ls", self.vimiv["commandline"].history)
        self.assertIn(":!echo foo_bar", self.vimiv["commandline"].history)
        self.assertIn(":!echo baz", self.vimiv["commandline"].history)
        # Set the text to :!e and search, should give the last two echos as
        # first results
        self.vimiv["commandline"].entry.set_text(":!e")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo baz")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo foo_bar")
        self.vimiv["commandline"].history_search(True)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo baz")

    def test_fail_hidden_command(self):
        """Fail running a hidden command."""
        self.vimiv["commandline"].entry.set_text(":command")
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.assertEqual(self.vimiv["statusbar"].left_label.get_text(),
                         "ERROR: No command called command")

    def tearDown(self):
        os.chdir(self.working_directory)
        self.vimiv["library"].reload(os.getcwd())


if __name__ == '__main__':
    main()
