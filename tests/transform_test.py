# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test transform.py for vimiv's test suite."""

import os
import shutil
import tempfile
from time import sleep
from unittest import main

from gi import require_version
require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

from vimiv_testcase import VimivTestCase


class TransformTest(VimivTestCase):
    """Transform Tests."""

    @classmethod
    def setUpClass(cls):
        if os.path.isdir("vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")
        shutil.copytree("vimiv/testimages", "vimiv/testimages_man")
        cls.init_test(cls, ["vimiv/testimages_man/arch-logo.png"])
        cls.transform = cls.vimiv["transform"]
        cls._waiting = False  # Used to wait for autorotate

    def test_get_images(self):
        """Get images to transform."""
        # Nothing marked -> current image
        expected_images = [self.vimiv.get_path()]
        received_images = self.transform.get_images("test")
        self.assertEqual(expected_images, received_images)
        # Marked images
        marked = ["arch-logo.png", "symlink_to_image"]
        marked = [os.path.abspath(image) for image in marked]
        self.vimiv["mark"].marked = marked
        received_images = self.transform.get_images("test")
        self.assertEqual(marked, received_images)
        # Reset mark
        self.vimiv["mark"].marked = []

    def test_delete_undelete(self):
        """Delete and undelete images."""
        # Delete from a higher index confirming we stay next to the deleted
        # index
        self.vimiv["image"].move_index(delta=2)
        path = self.vimiv.get_path()
        index = self.vimiv.get_index()
        self.assertTrue(os.path.exists(path))
        self.transform.delete()
        self.assertFalse(os.path.exists(path))
        # Undelete
        self.transform.undelete(os.path.basename(path))
        self.assertTrue(os.path.exists(path))
        # Test index here so undelete is always called
        self.assertEqual(self.vimiv.get_index(), index - 1)
        # Move back to beginning
        self.vimiv["image"].move_pos(forward=False)

    def test_fail_delete_undelete(self):
        """Fail deleting and undeleting images."""
        # Restore a non-existent file
        self.transform.undelete("foo_bar_baz")
        self.check_statusbar(
            "ERROR: Could not restore foo_bar_baz, file does not exist")
        # Restore a directory
        tmpdir = tempfile.mkdtemp()
        basename = os.path.basename(tmpdir)
        self.vimiv["transform"].trash_manager.delete(tmpdir)
        self.transform.undelete(basename)
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
        self.vimiv["transform"].trash_manager.delete(new_file)
        basename = os.path.basename(new_file)
        shutil.rmtree(tmpdir)
        self.transform.undelete(basename)
        self.check_statusbar(
            "ERROR: Could not restore %s, original directory is not accessible"
            % (basename))

    def test_rotate(self):
        """Rotate image."""
        # Before
        pixbuf = self.vimiv["image"].get_pixbuf()
        self.assertLess(pixbuf.get_height(), pixbuf.get_width())
        # Rotate
        self.transform.rotate(1)
        self.transform.apply()
        pixbuf = self.vimiv["image"].get_pixbuf()
        self.assertGreater(pixbuf.get_height(), pixbuf.get_width())
        while self.transform.threads_running:
            sleep(0.05)
        # Check file
        updated_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.vimiv.get_path())
        self.assertGreater(updated_pixbuf.get_height(),
                           updated_pixbuf.get_width())
        # Rotate back
        self.transform.rotate(-1)
        self.transform.apply()
        pixbuf = self.vimiv["image"].get_pixbuf()
        self.assertLess(pixbuf.get_height(), pixbuf.get_width())
        while self.transform.threads_running:
            sleep(0.05)
        # Check file
        updated_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.vimiv.get_path())
        self.assertLess(updated_pixbuf.get_height(), updated_pixbuf.get_width())
        # Fail because of no paths
        backup = list(self.vimiv.get_paths())
        self.vimiv.populate([])
        self.transform.rotate(1)
        self.check_statusbar("ERROR: No image to rotate")
        self.vimiv.populate(backup)
        ##################
        #  Command line  #
        ##################
        # Rotate
        self.run_command("rotate 1")
        pixbuf = self.vimiv["image"].get_pixbuf()
        self.assertGreater(pixbuf.get_height(), pixbuf.get_width())
        # Rotate back
        self.run_command("rotate -1")
        pixbuf = self.vimiv["image"].get_pixbuf()
        self.assertLess(pixbuf.get_height(), pixbuf.get_width())
        # Fail because of invalid argument
        self.run_command("rotate value")
        self.check_statusbar(
            "ERROR: Argument for rotate must be of type integer")

    def test_flip(self):
        """Flip image."""
        # Flip
        pixbuf_before = self.vimiv["image"].get_pixbuf()
        self.transform.flip(1)
        pixbuf_after = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_before, pixbuf_after)
        # Flip back
        self.transform.flip(1)
        pixbuf_after_2 = self.vimiv["image"].get_pixbuf()
        self.assertNotEqual(pixbuf_after, pixbuf_after_2)
        # Fail because of no paths
        backup = list(self.vimiv.get_paths())
        self.vimiv.populate([])
        self.transform.flip(1)
        self.check_statusbar("ERROR: No image to flip")
        self.vimiv.populate(backup)
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

    def test_auto_rotate(self):
        """Auto rotate images from transform checking messages."""
        self.transform.rotate_auto()
        # Wait for it to complete
        while self.transform.threads_running:
            sleep(0.05)
        self.assertIn("autorotate, 1 file",
                      self.vimiv["statusbar"].get_message())

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)
        if os.path.isdir("./vimiv/testimages_man"):
            shutil.rmtree("vimiv/testimages_man")


if __name__ == "__main__":
    main()
