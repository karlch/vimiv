# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test manipulate.py for vimiv's test suite."""

import os
import shutil
import tempfile
from time import sleep
from unittest import main

from PIL import Image

from vimiv_testcase import VimivTestCase, compare_images


class ManipulateTest(VimivTestCase):
    """Manipulate Tests."""

    @classmethod
    def setUpClass(cls):
        if os.path.isdir("vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")
        shutil.copytree("vimiv/testimages", "vimiv/testimages_man")
        cls.init_test(cls, ["vimiv/testimages_man/arch-logo.png"])
        cls.manipulate = cls.vimiv["manipulate"]

    def test_get_manipulated_images(self):
        """Get images to manipulate."""
        # Nothing marked -> current image
        expected_images = [self.vimiv.paths[self.vimiv.index]]
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(expected_images, received_images)
        # Marked images
        marked = ["arch-logo.png", "symlink_to_image"]
        marked = [os.path.abspath(image) for image in marked]
        self.vimiv["mark"].marked = marked
        received_images = self.manipulate.get_manipulated_images("test")
        self.assertEqual(marked, received_images)
        # Reset mark
        self.vimiv["mark"].marked = []

    def test_delete_undelete(self):
        """Delete and undelete images from within manipulate."""
        # Delete
        self.assertTrue(os.path.exists("arch-logo.png"))
        self.manipulate.delete()
        self.assertFalse(os.path.exists("arch-logo.png"))
        self.assertEqual(self.vimiv.paths[self.vimiv.index],
                         os.path.abspath("arch_001.jpg"))
        # Undelete
        self.manipulate.undelete("arch-logo.png")
        self.assertTrue(os.path.exists("arch-logo.png"))
        self.assertEqual(self.vimiv.paths[self.vimiv.index],
                         os.path.abspath("arch-logo.png"))

    def test_fail_delete_undelete(self):
        """Fail deleting and undeleting images."""
        # Restore a non-existent file
        self.manipulate.undelete("foo_bar_baz")
        self.check_statusbar(
            "ERROR: Could not restore foo_bar_baz, file does not exist")
        # Restore a directory
        tmpdir = tempfile.mkdtemp()
        basename = os.path.basename(tmpdir)
        self.vimiv["manipulate"].trash_manager.delete(tmpdir)
        self.manipulate.undelete(basename)
        self.check_statusbar(
            "ERROR: Could not restore %s, directories are not supported"
            % (basename))
        # Restore a file without a top directory
        tmpdir = tempfile.mkdtemp()
        extra_directory = os.path.join(tmpdir, "extra_directory")
        new_file = os.path.join(extra_directory, "new_file")
        os.mkdir(extra_directory)
        with open(new_file, "w") as f:
            f.write("")
        self.vimiv["manipulate"].trash_manager.delete(new_file)
        basename = os.path.basename(new_file)
        shutil.rmtree(tmpdir)
        self.manipulate.undelete(basename)
        self.check_statusbar(
            "ERROR: Could not restore %s, directory is not accessible"
            % (basename))

    def test_rotate(self):
        """Rotate image."""
        # Before
        pixbuf = self.vimiv["image"].get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertFalse(is_portrait)
        # Rotate
        self.manipulate.rotate(1, True)
        pixbuf = self.vimiv["image"].get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertTrue(is_portrait)
        # Rotate the file
        with Image.open(self.vimiv.paths[self.vimiv.index]) as im:
            self.assertFalse(im.width < im.height)
        self.assertIn(self.vimiv.paths[self.vimiv.index],
                      self.manipulate.simple_manipulations.keys())
        self.manipulate.thread_for_simple_manipulations()
        while self.manipulate.simple_manipulations.keys():
            sleep(0.05)
        with Image.open(self.vimiv.paths[self.vimiv.index]) as im:
            self.assertTrue(im.width < im.height)
        # Rotate back
        self.manipulate.rotate(1, True)
        pixbuf = self.vimiv["image"].get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertFalse(is_portrait)
        # Rotate the file
        self.assertIn(self.vimiv.paths[self.vimiv.index],
                      self.manipulate.simple_manipulations.keys())
        self.manipulate.thread_for_simple_manipulations()
        while self.manipulate.simple_manipulations.keys():
            sleep(0.05)
        with Image.open(self.vimiv.paths[self.vimiv.index]) as im:
            self.assertFalse(im.width < im.height)
        # Fail because of no paths
        backup = list(self.vimiv.paths)
        self.vimiv.paths = []
        self.manipulate.rotate(1, False)
        self.check_statusbar("ERROR: No image to rotate")
        self.vimiv.paths = backup
        ##################
        #  Command line  #
        ##################
        # Rotate
        self.run_command("rotate 1")
        pixbuf = self.vimiv["image"].get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertTrue(is_portrait)
        # Rotate back
        self.run_command("rotate -1")
        pixbuf = self.vimiv["image"].get_pixbuf()
        is_portrait = pixbuf.get_width() < pixbuf.get_height()
        self.assertFalse(is_portrait)
        # Fail because of invalid argument
        self.run_command("rotate value")
        self.check_statusbar(
            "ERROR: Argument for rotate must be of type integer")

    def test_flip(self):
        """Flip image."""
        # Flip
        pixbuf_before = self.vimiv["image"].get_pixbuf()
        self.manipulate.flip(1, False)
        pixbuf_after = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_before, pixbuf_after)
        # Flip back
        self.manipulate.flip(1, False)
        pixbuf_after_2 = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_after, pixbuf_after_2)
        # Fail because of no paths
        backup = list(self.vimiv.paths)
        self.vimiv.paths = []
        self.manipulate.flip(1, False)
        self.check_statusbar("ERROR: No image to flip")
        self.vimiv.paths = backup
        ##################
        #  Command line  #
        ##################
        # Flip
        self.run_command("flip 1")
        pixbuf_after_3 = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_after_2, pixbuf_after_3)
        # Flip back
        self.run_command("flip 1")
        pixbuf_after_4 = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_after_3, pixbuf_after_4)
        # Fail because of invalid argument
        self.run_command("flip value")
        self.check_statusbar("ERROR: Argument for flip must be of type integer")

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
        # Close via button
        self.manipulate.toggle()
        self.manipulate.button_clicked(None, False)
        self.assertFalse(self.manipulate.sliders["bri"].is_focus())
        self.assertTrue(self.vimiv["main_window"].is_focus())

    def test_manipulate_image(self):
        """Test manipulate image."""
        # Copy image before manipulation
        tmpfile = "tmp.jpg"
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        shutil.copyfile(self.vimiv.paths[self.vimiv.index], tmpfile)
        # Leaving with False should not change the image
        self.manipulate.toggle()
        self.manipulate.manipulations = {"bri": 20, "con": 20, "sha": 20}
        self.manipulate.button_clicked(None, False)
        self.assertTrue(compare_images(tmpfile,
                                       self.vimiv.paths[self.vimiv.index]))
        # Image is different to copied backup after manipulations
        self.manipulate.toggle()
        self.manipulate.manipulations = {"bri": 20, "con": 20, "sha": 20}
        self.manipulate.button_clicked(None, True)
        self.assertFalse(compare_images(tmpfile,
                                        self.vimiv.paths[self.vimiv.index]))

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
        self.manipulate.button_clicked(None, False)

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
        self.manipulate.manipulations = {"bri": 1, "con": 1, "sha": 1}
        self.assertEqual(0, self.manipulate.check_for_edit(False))
        self.manipulate.manipulations = {"bri": 10, "con": 0, "sha": 0}
        self.assertEqual(1, self.manipulate.check_for_edit(False))
        self.assertEqual(0, self.manipulate.check_for_edit(True))

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)
        if os.path.isdir("./vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")


if __name__ == "__main__":
    main()
