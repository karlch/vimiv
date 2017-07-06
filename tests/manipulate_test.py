# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test manipulate.py for vimiv's test suite."""

import os
import shutil
from unittest import main

from vimiv_testcase import VimivTestCase, compare_files


class ManipulateTest(VimivTestCase):
    """Manipulate Tests."""

    @classmethod
    def setUpClass(cls):
        if os.path.isdir("vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")
        shutil.copytree("vimiv/testimages", "vimiv/testimages_man")
        cls.init_test(cls, ["vimiv/testimages_man/arch-logo.png"])
        cls.manipulate = cls.vimiv["manipulate"]

    def test_toggle(self):
        """Toggle manipulate."""
        # Via function
        self.manipulate.toggle()
        self.assertTrue(self.manipulate.is_visible())
        self.assertTrue(self.manipulate.sliders["bri"].is_focus())
        self.manipulate.toggle()
        self.assertFalse(self.manipulate.is_visible())
        self.assertFalse(self.manipulate.sliders["bri"].is_focus())
        self.assertTrue(self.vimiv["main_window"].is_focus())
        # Close
        self.manipulate.toggle()
        self.manipulate.finish(False)
        self.assertFalse(self.manipulate.sliders["bri"].is_focus())
        self.assertTrue(self.vimiv["main_window"].is_focus())

    def test_manipulate_image(self):
        """Test manipulate image."""
        # Copy image before manipulation
        tmpfile = "tmp.jpg"
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        shutil.copyfile(self.vimiv.get_path(), tmpfile)
        # Leaving with False should not change the image
        self.manipulate.toggle()
        self.manipulate.cmd_edit("bri", "20")
        self.manipulate.finish(False)
        self.assertTrue(compare_files(tmpfile, self.vimiv.get_path()))
        # Image is different to copied backup after manipulations
        self.manipulate.toggle()
        self.manipulate.cmd_edit("bri", "20")
        self.manipulate.finish(True)
        self.assertFalse(compare_files(tmpfile, self.vimiv.get_path()))

    def test_focus_sliders(self):
        """Focusing sliders in manipulate."""
        self.manipulate.toggle()
        self.assertTrue(self.manipulate.sliders["bri"].is_focus())
        self.manipulate.focus_slider("con")
        self.assertTrue(self.manipulate.sliders["con"].is_focus())
        self.manipulate.focus_slider("sha")
        self.assertTrue(self.manipulate.sliders["sha"].is_focus())
        self.manipulate.focus_slider("bri")
        self.assertTrue(self.manipulate.sliders["bri"].is_focus())
        # Slider does not exist
        self.manipulate.focus_slider("val")
        self.check_statusbar("ERROR: No slider called val")
        # Leave
        self.manipulate.finish(False)

    def test_change_slider_value(self):
        """Change slider value in manipulate."""
        # Change value
        self.manipulate.toggle()
        self.manipulate.focus_slider("bri")
        self.manipulate.change_slider(-1)
        received_value = self.manipulate.sliders["bri"].get_value()
        self.assertEqual(received_value, -1)
        # Change value with a numstr
        self.vimiv["eventhandler"].num_str = "5"
        self.manipulate.change_slider(2)
        received_value = self.manipulate.sliders["bri"].get_value()
        self.assertEqual(received_value, -1 + 2 * 5)
        # Not an integer
        self.manipulate.change_slider("hi")
        self.check_statusbar(
            "ERROR: Argument for slider must be of type integer")
        received_value = self.manipulate.sliders["bri"].get_value()
        self.assertEqual(received_value, -1 + 2 * 5)

    def test_cmd_edit(self):
        """Test manipulating from command line commands."""
        # Just call the function
        self.manipulate.cmd_edit("sha", "20")
        self.assertEqual(self.manipulate.sliders["sha"].get_value(), 20)
        self.assertTrue(self.manipulate.sliders["sha"].is_focus())
        # Set contrast via command line
        self.run_command("set contrast 35")
        self.assertEqual(self.manipulate.sliders["con"].get_value(), 35)
        self.assertTrue(self.manipulate.sliders["con"].is_focus())
        # No argument means 0
        self.run_command("set contrast")
        self.assertEqual(self.manipulate.sliders["con"].get_value(), 0)
        # Close via command line
        self.run_command("discard_changes")
        self.assertFalse(self.manipulate.sliders["sha"].is_focus())
        # Error: not a valid integer for manipulation
        self.run_command("set brightness value")
        self.assertFalse(self.manipulate.sliders["bri"].is_focus())
        self.check_statusbar("ERROR: Argument must be of type integer")

    def test_check_for_edit(self):
        """Check if an image was edited."""
        self.manipulate.finish(False)
        self.assertEqual(0, self.manipulate.check_for_edit(False))
        self.manipulate.cmd_edit("bri", "10")
        self.assertEqual(1, self.manipulate.check_for_edit(False))
        self.assertEqual(0, self.manipulate.check_for_edit(True))

    def test_quit_with_edited_image(self):
        """Quit vimiv with an edited image."""
        self.manipulate.cmd_edit("bri", "10")
        self.vimiv.quit_wrapper()
        self.check_statusbar("WARNING: Image has been edited, add ! to force")
        self.manipulate.finish(False)

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)
        if os.path.isdir("./vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")


if __name__ == "__main__":
    main()
