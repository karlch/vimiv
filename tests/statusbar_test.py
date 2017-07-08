# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Statusbar tests for vimiv's test suite."""

from unittest import main

from vimiv_testcase import VimivTestCase, refresh_gui


class StatusbarTest(VimivTestCase):
    """Statusbar Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.statusbar = cls.vimiv["statusbar"]

    def test_toggle_statusbar(self):
        """Toggle the statusbar."""
        self.assertTrue(self.statusbar.is_visible())
        self.assertTrue(self.settings["display_bar"].get_value())
        # Hide
        self.run_command("set display_bar!")
        self.assertFalse(self.statusbar.is_visible())
        self.assertFalse(self.settings["display_bar"].get_value())
        # Show again
        self.run_command("set display_bar!")
        self.assertTrue(self.statusbar.is_visible())
        self.assertTrue(self.settings["display_bar"].get_value())

    def test_message(self):
        """Show a message."""
        self.statusbar.message("Test error", "error")
        self.check_statusbar("ERROR: Test error")
        self.statusbar.message("Test warning", "warning")
        self.check_statusbar("WARNING: Test warning")
        self.statusbar.message("Test info", "info", timeout=0.01)
        self.check_statusbar("INFO: Test info")
        # Remove error message
        refresh_gui(0.015)
        self.assertNotEqual(self.statusbar.get_message(),
                            "INFO: Test info")

    def test_hidden_message(self):
        """Show an error message with an initially hidden statusbar."""
        # Hide
        self.run_command("set display_bar!")
        self.assertFalse(self.statusbar.is_visible())
        # Send an error message
        self.statusbar.message("Test error")
        self.check_statusbar("ERROR: Test error")
        self.assertTrue(self.statusbar.is_visible())
        # Remove error message
        self.statusbar.update_info()
        self.assertNotEqual(self.statusbar.get_message(),
                            "ERROR: Test error")
        self.assertFalse(self.statusbar.is_visible())
        # Show again
        self.run_command("set display_bar!")
        self.assertTrue(self.statusbar.is_visible())

    def test_clear_status(self):
        """Clear num_str, search and error message."""
        self.vimiv["eventhandler"].set_num_str(42)
        self.vimiv["commandline"].search.results = ["Something"]
        self.statusbar.message("Catastrophe", "error")
        self.check_statusbar("ERROR: Catastrophe")
        self.statusbar.clear_status()
        self.assertFalse(self.vimiv["eventhandler"].get_num_str())
        self.assertFalse(self.vimiv["commandline"].search.results)
        self.assertNotEqual(self.vimiv["statusbar"].get_message(),
                            "Error: Catastrophe")


if __name__ == "__main__":
    main()
