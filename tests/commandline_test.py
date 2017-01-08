# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
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
        self.run_command("set overzoom!")
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)

    def test_run_alias(self):
        """Run an alias."""
        self.vimiv.aliases = {"test_alias": "set overzoom!"}
        before_command = self.vimiv["image"].overzoom
        self.run_command("test_alias")
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)
        # Alias that does not exist
        self.vimiv.aliases = {"test_alias": "useless_command"}
        self.run_command("test_alias")
        self.check_statusbar("ERROR: No command called useless_command")

    def test_run_external(self):
        """Run an external command and test failures."""
        # Run command
        self.run_command("!touch tmp_foo", True)
        files = os.listdir()
        self.assertTrue("tmp_foo" in files)
        os.remove("tmp_foo")
        # Try to run a non-existent command
        self.run_command("!foo_bar_baz", True)
        # self.run_command("!sleep 10", True)
        self.check_statusbar("ERROR: /bin/sh: foo_bar_baz: command not found")

    def test_pipe(self):
        """Pipe a command to vimiv."""
        # Internal command
        before_command = self.vimiv["image"].overzoom
        self.run_command("!echo set overzoom! |", True)
        refresh_gui(0.001)
        after_command = self.vimiv["image"].overzoom
        self.assertNotEqual(before_command, after_command)
        # Directory
        expected_dir = os.path.abspath("./vimiv/testimages/")
        self.run_command("!echo vimiv/testimages |", True)
        refresh_gui(0.001)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Image
        expected_image = os.path.abspath("arch_001.jpg")
        self.run_command("!echo arch_001.jpg |", True)
        refresh_gui()
        self.assertEqual(self.vimiv.paths[0], expected_image)

    def test_path(self):
        """Enter a path in the commandline."""
        # Pass a directory
        expected_dir = os.path.abspath("./vimiv/testimages")
        self.run_command("./vimiv/testimages")
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Pass an image
        expected_image = os.path.abspath("arch-logo.png")
        self.run_command("./arch-logo.png")
        self.assertEqual(self.vimiv.paths[0], expected_image)

    def test_search(self):
        """Search for images, directories and navigate search results."""
        self.vimiv["commandline"].incsearch = False
        self.vimiv["commandline"].cmd_search()
        self.assertEqual(self.vimiv["commandline"].entry.get_text(), "/")
        # Search should move into testimages
        expected_dir = os.path.abspath("./vimiv")
        self.run_search("vimi")
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        expected_dir = os.path.abspath("./testimages")
        self.run_search("test")
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Search should have these results
        self.vimiv["commandline"].search_case = False
        self.run_search("Ar")
        expected_search_results = [1, 2]
        search_results = self.vimiv["commandline"].search_positions
        self.assertEqual(search_results, expected_search_results)
        # Moving forward to next result should work
        self.assertEqual(self.vimiv.get_pos(), 1)
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(), 2)
        # Forward should wrap
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(), 1)
        # Backward should wrap again
        self.vimiv["commandline"].search_move(forward=False)
        self.assertEqual(self.vimiv.get_pos(), 2)
        # Backward to one again
        self.vimiv["commandline"].search_move(forward=False)
        self.assertEqual(self.vimiv.get_pos(), 1)
        # Deliberately move to last element in library
        self.vimiv["library"].move_pos()
        self.assertNotEqual(self.vimiv.get_pos(), 1)
        # Moving forward should wrap to 1
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(), 1)
        # Deliberately move to first element in library
        self.vimiv["library"].move_pos(forward=False)
        self.assertEqual(self.vimiv.get_pos(), 0)
        # Moving forward should go to 1
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(), 1)
        # Searching case sensitively should have no results here
        self.vimiv["commandline"].search_case = True
        self.run_search("Ar")
        self.assertFalse(self.vimiv["commandline"].search_positions)
        # Search move should give an error message without any results
        self.vimiv["commandline"].search_move()
        self.check_statusbar("WARNING: No search results")

    def test_incsearch(self):
        """Incsearch."""
        self.vimiv["commandline"].incsearch = True
        dir_before = os.getcwd()
        file_before = self.vimiv.get_pos(True)
        self.vimiv["commandline"].cmd_search()
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
        self.vimiv["commandline"].leave(True)
        self.assertEqual(os.getcwd(), dir_before)
        self.assertEqual(self.vimiv.get_pos(True), file_before)
        self.assertFalse(self.vimiv["commandline"].search_positions)
        # Move into a more interesting directory
        self.vimiv["library"].move_up("vimiv/testimages")
        # First search should stay at animation
        self.vimiv["commandline"].cmd_search()
        self.vimiv["commandline"].entry.set_text("/a")
        self.assertEqual(self.vimiv.get_pos(True, "lib"), "animation")
        # Now move to arch-logo
        self.vimiv["commandline"].entry.set_text("/arch")
        self.assertEqual(self.vimiv.get_pos(True, "lib"), "arch-logo.png")
        # Accept
        self.vimiv["commandline"].handler(self.vimiv["commandline"].entry)
        self.assertEqual(self.vimiv.get_pos(True), "arch-logo.png")
        # Move to the next result as a final check
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(True), "arch_001.jpg")

    def test_alias(self):
        """Add an alias."""
        self.vimiv["commandline"].alias("testalias")
        self.assertTrue("testalias" in self.vimiv.aliases)

    def test_history_search(self):
        """Search through history."""
        # Clear history so the commands are not here from previous sessions
        self.vimiv["commandline"].history = []
        self.assertFalse(self.vimiv["commandline"].history)
        # First run some very fast commands
        self.run_command("!ls > /dev/null", True)
        self.run_command("!echo foo_bar > /dev/null", True)
        self.run_command("!echo baz > /dev/null", True)
        # Check if they were added to the history correctly
        self.assertIn(":!ls > /dev/null", self.vimiv["commandline"].history)
        self.assertIn(":!echo foo_bar > /dev/null",
                      self.vimiv["commandline"].history)
        self.assertIn(":!echo baz > /dev/null",
                      self.vimiv["commandline"].history)
        # Set the text to :!e and search, should give the last two echos as
        # first results
        self.vimiv["commandline"].entry.set_text(":!e")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo baz > /dev/null")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo foo_bar > /dev/null")
        self.vimiv["commandline"].history_search(True)
        self.assertEqual(self.vimiv["commandline"].entry.get_text(),
                         ":!echo baz > /dev/null")

    def test_fail_hidden_command(self):
        """Fail running a hidden command."""
        self.run_command("command")
        self.check_statusbar("ERROR: No command called command")

    def tearDown(self):
        os.chdir(self.working_directory)
        self.vimiv["library"].reload(os.getcwd())


if __name__ == '__main__':
    main()
