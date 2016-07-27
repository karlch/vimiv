#!/usr/bin/env python
# encoding: utf-8

import os
from unittest import TestCase, main
import vimiv.parser as parser

class ParserTest(TestCase):

    def setUp(self):
        self.parser = parser.get_args()
        self.config_settings = parser.parse_config()

    def test_parse_dirs(self):
        parser.parse_dirs()
        vimivdir = os.path.join(os.path.expanduser('~'), ".vimiv")
        trashdir = os.path.join(vimivdir, "Trash")
        tagdir = os.path.join(vimivdir, "Tags")
        thumbdir = os.path.join(vimivdir, "Thumbnails")
        for directory in [vimivdir, trashdir, tagdir, thumbdir]:
            self.assertTrue(os.path.isdir(directory))

    def test_parse_config(self):
        general = self.config_settings["GENERAL"]
        library = self.config_settings["LIBRARY"]
        amount_general_settings = len(general.keys())
        amount_library_settings = len(library.keys())
        self.assertEqual(amount_general_settings, 14)
        self.assertEqual(amount_library_settings, 9)
        self.assertFalse(general["start_fullscreen"])
        self.assertEqual(general["slideshow_delay"], 2)
        self.assertTrue(general["display_bar"])
        self.assertEqual(library["file_check_amount"], 30)

    def test_parse_args(self):
        # Set arguments to be different from default so they are run
        args = ["--slideshow-delay", "5", "-B", "-l", "-r", "-g", "foo"]
        settings = parser.parse_args(self.parser, self.config_settings, args)
        general = settings["GENERAL"]
        self.assertFalse(general["display_bar"])
        self.assertEqual(general["slideshow_delay"], 5)

    def test_parse_keys(self):
        keybindings = parser.parse_keys()
        image_bindings = keybindings["IMAGE"]
        self.assertEqual(image_bindings["j"], "down")

if __name__ == '__main__':
    main()
