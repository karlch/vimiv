#!/usr/bin/env python
# encoding: utf-8
"""Parser Tests for vimiv's testsuite."""

import os
from unittest import TestCase, main
import vimiv.configparser as parser


class ParserTest(TestCase):
    """Different parsers from parser.py test."""

    def setUp(self):
        self.config_settings = parser.parse_config()

    def test_parse_dirs(self):
        """Check if all directories where created correctly."""
        parser.parse_dirs()
        vimivdir = os.path.join(os.path.expanduser('~'), ".vimiv")
        trashdir = os.path.join(vimivdir, "Trash")
        tagdir = os.path.join(vimivdir, "Tags")
        thumbdir = os.path.join(vimivdir, "Thumbnails")
        for directory in [vimivdir, trashdir, tagdir, thumbdir]:
            self.assertTrue(os.path.isdir(directory))

    def test_parse_config(self):
        """Check if the config files where parsed correctly."""
        general = self.config_settings["GENERAL"]
        library = self.config_settings["LIBRARY"]
        amount_general_settings = len(general.keys())
        amount_library_settings = len(library.keys())
        self.assertEqual(amount_general_settings, 17)
        self.assertEqual(amount_library_settings, 8)
        self.assertFalse(general["start_fullscreen"])
        self.assertEqual(general["slideshow_delay"], 2)
        self.assertTrue(general["display_bar"])
        self.assertEqual(library["file_check_amount"], 30)

    def test_parse_args(self):
        """Check if command line arguments are parsed correctly."""
        # Set arguments to be different from default so they are run
        # TODO do this with Gtk
        pass
        # args = ["--slideshow-delay", "5", "-B", "-l", "-r", "-g", "foo"]
        # settings = parser.parse_args(self.parser, self.config_settings, args)
        # general = settings["GENERAL"]
        # self.assertFalse(general["display_bar"])
        # self.assertEqual(general["slideshow_delay"], 5)

    def test_parse_keys(self):
        """Check if the keybindings are parsed correctly."""
        keybindings = parser.parse_keys()
        image_bindings = keybindings["IMAGE"]
        self.assertEqual(image_bindings["j"], "down")


if __name__ == '__main__':
    main()
