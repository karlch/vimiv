# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Statusbar tests for vimiv's test suite."""

from unittest import main

from vimiv_testcase import VimivTestCase


class StatusbarTest(VimivTestCase):
    """Statusbar Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.statusbar = cls.vimiv["statusbar"]
        # Remove the initial library error
        cls.statusbar.error_false()

    def test_toggle_statusbar(self):
        """Toggle the statusbar."""
        self.assertTrue(self.statusbar.is_visible())
        self.assertFalse(self.statusbar.hidden)
        # Hide
        self.statusbar.toggle()
        self.assertFalse(self.statusbar.is_visible())
        self.assertTrue(self.statusbar.hidden)
        # Show again
        self.statusbar.toggle()
        self.assertTrue(self.statusbar.is_visible())
        self.assertFalse(self.statusbar.hidden)

    def test_message(self):
        """Show a message."""
        self.statusbar.message("Test error", "error")
        self.check_statusbar("ERROR: Test error")
        self.statusbar.message("Test warning", "warning")
        self.check_statusbar("WARNING: Test warning")
        self.statusbar.message("Test info", "info")
        self.check_statusbar("INFO: Test info")
        # Timer is running
        self.assertGreater(self.statusbar.timer_id, 0)
        # Remove error message by hand
        self.statusbar.update_info()
        self.assertNotEqual(self.statusbar.left_label.get_text(),
                            "INFO: Test info")

    def test_hidden_message(self):
        """Show an error message with an initially hidden statusbar."""
        # Hide
        self.statusbar.toggle()
        self.assertFalse(self.statusbar.is_visible())
        # Send an error message
        self.statusbar.message("Test error")
        self.check_statusbar("ERROR: Test error")
        self.assertTrue(self.statusbar.is_visible())
        # Remove error message
        self.statusbar.update_info()
        self.assertNotEqual(self.statusbar.left_label.get_text(),
                            "ERROR: Test error")
        self.assertFalse(self.statusbar.is_visible())
        # Show again
        self.statusbar.toggle()
        self.assertTrue(self.statusbar.is_visible())

    def test_clear_status(self):
        """Clear num_str, search and error message."""
        self.vimiv["eventhandler"].num_str = "42"
        self.vimiv["commandline"].search_positions = [1, 2, 3]
        self.statusbar.message("Catastrophe", "error")
        self.check_statusbar("ERROR: Catastrophe")
        self.statusbar.clear_status()
        self.assertEqual(self.vimiv["eventhandler"].num_str, "")
        self.assertFalse(self.vimiv["commandline"].search_positions)
        self.assertNotEqual(self.vimiv["statusbar"].left_label.get_text(),
                            "Error: Catastrophe")


if __name__ == "__main__":
    main()
