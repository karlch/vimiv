# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tests for log for vimiv's test suite."""

import os
import sys
from unittest import main

from gi import require_version
require_version('Gdk', '3.0')
from gi.repository import Gdk

from vimiv_testcase import VimivTestCase


class LogTest(VimivTestCase):
    """Log Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, debug=True)
        cls.logfile = os.path.join(cls.vimiv.directory, "vimiv.log")

    def test_creation(self):
        """Creation and header of the log file."""
        self.assertTrue(os.path.isfile(self.logfile))
        content = self.read_log()
        self.assertIn(self.logfile.replace(os.environ["HOME"], "~"), content)
        self.assertIn("[Version]", content)
        self.assertIn("[Python]", content)
        self.assertIn("[GTK]", content)

    def test_write(self):
        """Write message to log."""
        self.vimiv["log"].write_message("Title", "Message")
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[Title]", "Message"))
        # Message containing time
        self.vimiv["log"].write_message("Date", "time")
        last_line = self.read_log(string=False)[-1]
        self.assertNotIn("time", last_line)

    def test_write_separator(self):
        """Write separator line to log."""
        self.vimiv["log"].write_separator()
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "#" * 80 + "\n")

    def test_write_to_stderr(self):
        """Write to stderr and therefore to log."""
        sys.stderr.write("Traceback\nA great catastrophe")
        lines = self.read_log(string=False)
        self.assertIn("[stderr]", lines[-3])
        self.assertIn("Traceback", lines[-2])
        self.assertIn("A great catastrophe", lines[-1])

    def test_debug_mode_command(self):
        """Run a command in debug mode and therefore log it."""
        self.run_command("!:")
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[commandline]", ":!:"))

    def test_debug_mode_statusbar(self):
        """Statusbar message in debug mode and therefore log it."""
        self.vimiv["statusbar"].message("Useful", "info")
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[info]", "Useful"))

    def test_debug_mode_eventhandler(self):
        """Run keybinding and mouse click in debug mode and therefore log it."""
        # Keybinding
        event = Gdk.Event().new(Gdk.EventType.KEY_PRESS)
        event.keyval = Gdk.keyval_from_name("j")
        self.vimiv["library"].treeview.emit("key_press_event", event)
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[key]", "j: scroll_lib j"))
        # Mouse click
        event = Gdk.Event().new(Gdk.EventType.BUTTON_PRESS)
        event.button = 1
        self.vimiv["window"].emit("button_press_event", event)
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[key]", "Button1: next"))

    def test_debug_mode_numstr(self):
        """Add and clear num_str in debug mode and therefore log it."""
        self.vimiv.debug = True
        self.vimiv["eventhandler"].num_append("3")
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[number]", "3->3"))
        self.vimiv["eventhandler"].num_clear()
        last_line = self.read_log(string=False)[-1]
        self.assertEqual(last_line, "%-15s %s\n" % ("[number]", "cleared"))

    def read_log(self, string=True):
        """Read log to string and return the string.

        Args:
            string: If True, return content as string, else return lines as
                list.
        """
        with open(self.logfile) as f:
            if string:
                content = f.read()
            else:
                content = f.readlines()
        return content


if __name__ == "__main__":
    main()
