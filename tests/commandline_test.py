# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Command line tests for vimiv's test suite."""

import os
import tempfile
import shutil
from subprocess import Popen, PIPE
from unittest import main

from vimiv.settings import settings

from vimiv_testcase import VimivTestCase, refresh_gui


class CommandlineTest(VimivTestCase):
    """Command Line Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.search = cls.vimiv["commandline"].search

    def setUp(self):
        self.working_directory = os.getcwd()

    def tearDown(self):
        os.chdir(self.working_directory)
        self.vimiv["library"].reload(os.getcwd())


class FastCommandlineTest(CommandlineTest):
    """Runs the fast command line tests which do not have long extra threads."""

    def test_toggling(self):
        """Open and leave the commandline."""
        # Focusing
        self.vimiv["commandline"].enter()
        self.assertEqual(self.vimiv["commandline"].get_text(), ":")
        self.assertTrue(self.vimiv["commandline"].is_focus())
        self.assertTrue(self.vimiv["commandline"].is_visible())
        # Leaving by deleting the colon
        self.vimiv["commandline"].set_text("")
        self.assertFalse(self.vimiv["commandline"].is_visible())
        self.assertFalse(self.vimiv["commandline"].is_focus())
        # Focusing with text
        self.vimiv["commandline"].enter("test")
        self.assertEqual(self.vimiv["commandline"].get_text(), ":test")
        self.assertTrue(self.vimiv["commandline"].is_focus())
        self.assertTrue(self.vimiv["commandline"].is_visible())
        # Leaving normally
        self.vimiv["commandline"].leave()
        self.assertFalse(self.vimiv["commandline"].is_visible())
        self.assertFalse(self.vimiv["commandline"].is_focus())

    def test_run_command(self):
        """Run an internal vimiv command."""
        before_command = self.settings["show_hidden"].get_value()
        self.run_command("set show_hidden!")
        after_command = self.settings["show_hidden"].get_value()
        self.assertNotEqual(before_command, after_command)

    def test_run_command_with_prefix(self):
        """Run an internal vimiv command with [COUNT] prefix."""
        self.run_command("2first_lib")
        self.assertEqual(self.vimiv.get_pos(), 1)
        self.run_command("first_lib")
        self.assertEqual(self.vimiv.get_pos(), 0)

    def test_run_empty_command(self):
        """Run an empty command."""
        self.run_command("")
        self.assertFalse(self.vimiv["commandline"].is_focus())

    def test_run_alias(self):
        """Run an alias."""
        self.vimiv["commandline"].commands.add_alias("test", "set show_hidden!")
        before_command = settings["show_hidden"].get_value()
        self.run_command("test")
        after_command = settings["show_hidden"].get_value()
        self.assertNotEqual(before_command, after_command)

    def test_run_external(self):
        """Run an external command and test failures."""
        # Run command
        self.run_command("!touch tmp_foo", True)
        files = os.listdir()
        self.assertTrue("tmp_foo" in files)
        os.remove("tmp_foo")
        # Try to run a non-existent command
        fail_command = "foo_bar_baz"
        p = Popen(fail_command, stdout=PIPE, stderr=PIPE, shell=True)
        _, err_message = p.communicate()
        err_message = err_message.decode()
        self.run_command("!foo_bar_baz", True)
        refresh_gui()  # Needed because of GLib.idle_add in command thread
        self.check_statusbar("ERROR: Command exited with status 127\n" +
                             err_message)

    def test_add_alias(self):
        """Add an alias."""
        self.vimiv["commandline"].commands.add_alias("test", "!ls")
        self.assertIn("test", self.vimiv["commandline"].commands.aliases)
        self.assertEqual(self.vimiv["commandline"].commands.aliases["test"],
                         "!ls")

    def test_fail_add_alias(self):
        """Fail adding an alias."""
        self.vimiv["commandline"].commands.add_alias("test", "foo_bar_baz")
        self.assertNotIn("test", self.vimiv["commandline"].commands.aliases)
        self.check_statusbar(
            'ERROR: Alias "test" failed: no command called "foo_bar_baz"')
        self.vimiv["commandline"].commands.add_alias("first_lib", "!ls")
        self.assertNotIn("first_lib",
                         self.vimiv["commandline"].commands.aliases)
        self.check_statusbar(
            'ERROR: Alias "first_lib" would overwrite an existing command')

    def test_history_search(self):
        """Search through history."""
        # First run some very fast commands
        self.run_command("!ls > /dev/null", True)
        self.run_command("!echo foo_bar > /dev/null", True)
        self.run_command("!echo baz > /dev/null", True)
        # Check if they were added to the history correctly
        self.assertIn(":!ls > /dev/null",
                      self.vimiv["commandline"].get_history())
        self.assertIn(":!echo foo_bar > /dev/null",
                      self.vimiv["commandline"].get_history())
        self.assertIn(":!echo baz > /dev/null",
                      self.vimiv["commandline"].get_history())
        # Set the text to :!e and search, should give the last two echos as
        # first results
        self.vimiv["commandline"].set_text(":!e")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].get_text(),
                         ":!echo baz > /dev/null")
        self.vimiv["commandline"].history_search(False)
        self.assertEqual(self.vimiv["commandline"].get_text(),
                         ":!echo foo_bar > /dev/null")
        self.vimiv["commandline"].history_search(True)
        self.assertEqual(self.vimiv["commandline"].get_text(),
                         ":!echo baz > /dev/null")

    def test_fail_hidden_command(self):
        """Fail running a hidden command."""
        self.run_command("command")
        self.check_statusbar(
            "ERROR: Called a hidden command from the command line")

    def test_fail_path_command(self):
        """Try accessing an invalid path."""
        self.run_command("./foo_bar_baz/baz_bar_foo/vimiv")
        self.check_statusbar("ERROR: Not a valid path")

    def test_fail_pipe(self):
        """Run invalid pipes."""
        self.run_command("!echo |")
        refresh_gui()
        self.check_statusbar("INFO: No input from pipe")
        self.run_command("!find . -type f -maxdepth 1 |")
        refresh_gui()
        self.check_statusbar("INFO: No image found")

    def tearDown(self):
        self.vimiv["commandline"].commands.aliases.clear()


class SlowCommandlineTest(CommandlineTest):
    """Runs the slow command line tests which have long extra threads."""

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
        refresh_gui()
        self.assertEqual(self.vimiv.get_path(), expected_image)
        # Pass an image in another directory
        testimage = tempfile.NamedTemporaryFile()
        shutil.copyfile(expected_image, testimage.name)
        self.run_command(testimage.name)
        refresh_gui()
        self.assertEqual(self.vimiv.get_path(), testimage.name)
        self.assertEqual(os.getcwd(), os.path.dirname(testimage.name))

    def test_pipe(self):
        """Pipe a command to vimiv."""
        # Internal command
        before_command = self.settings["show_hidden"].get_value()
        self.run_command("!echo set show_hidden! |", True)
        refresh_gui()
        after_command = self.settings["show_hidden"].get_value()
        self.assertNotEqual(before_command, after_command)
        # Directory
        expected_dir = os.path.abspath("./vimiv/testimages/")
        self.run_command("!echo vimiv/testimages |", True)
        refresh_gui()
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Image
        expected_image = os.path.abspath("arch_001.jpg")
        self.run_command("!echo arch_001.jpg |", True)
        refresh_gui()
        self.assertEqual(self.vimiv.get_path(), expected_image)


class SearchTest(CommandlineTest):
    """Test the integration of search with the rest of vimiv."""

    def test_search(self):
        """Search for images, directories and navigate search results."""
        # Search should move into testimages
        expected_dir = os.path.abspath("vimiv")
        self.run_search("vimi")
        self.assertEqual(expected_dir, os.getcwd())
        expected_dir = os.path.abspath("testimages")
        self.run_search("test")
        self.assertEqual(expected_dir, os.getcwd())
        # Search should have these results
        self.run_command("set search_case_sensitive!")
        self.run_search("Ar")
        expected_search_results = ["arch-logo.png", "arch_001.jpg"]
        self.assertEqual(self.search.results, expected_search_results)
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
        self.run_command("set search_case_sensitive!")
        self.run_search("Ar")
        self.assertFalse(self.search.results)
        # Search move should give an error message without any results
        self.vimiv["commandline"].search_move()
        self.check_statusbar('INFO: No file matching "Ar"')

    def test_incsearch(self):
        """Incsearch."""
        self.run_command("set incsearch!")
        dir_before = os.getcwd()
        self.vimiv["commandline"].enter_search()
        # Search should be done automatically
        self.vimiv["commandline"].set_text("/vi")
        self.assertEqual(self.search.results, ["vimiv"])
        self.run_command("set incsearch!")
        position = self.vimiv["library"].get_position()
        focused_file = self.vimiv["library"].files[position]
        self.assertEqual(focused_file, "vimiv")
        self.run_command("set incsearch!")
        # Not accepted -> Back to the default position
        self.vimiv["commandline"].leave(True)
        self.assertEqual(os.getcwd(), dir_before)
        self.assertEqual(self.vimiv.get_pos(), 0)
        self.assertFalse(self.search.results)
        # Move into a more interesting directory
        self.vimiv["library"].move_up("vimiv/testimages")
        # First search should move to arch-logo
        self.vimiv["commandline"].enter_search()
        self.vimiv["commandline"].set_text("/a")
        self.assertEqual(
            self.vimiv["library"].files[self.vimiv["library"].get_position()],
            "arch-logo.png")
        # Should stay there upon longer typing
        self.vimiv["commandline"].set_text("/arch")
        self.assertEqual(
            self.vimiv["library"].files[self.vimiv["library"].get_position()],
            "arch-logo.png")
        # Accept
        self.vimiv["commandline"].emit("activate")
        self.assertEqual(self.vimiv.get_pos(True), "arch-logo.png")
        # Move to the next result as a final check
        self.vimiv["commandline"].search_move(forward=True)
        self.assertEqual(self.vimiv.get_pos(True), "arch_001.jpg")

    def test_fail_search_move(self):
        """Fail moving in search as there is no search."""
        self.vimiv["library"].reload(".")  # Reset
        self.vimiv["commandline"].search_move(forward=True)
        self.check_statusbar("ERROR: No search results to navigate")


if __name__ == "__main__":
    main()
