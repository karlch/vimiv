#!/usr/bin/env python
# encoding: utf-8

import os
from unittest import TestCase
import vimiv.parser as parser

class MyViewTest(TestCase):

    def setUp(self):
        self.parser = parser.get_args()
        self.args = self.parser.parse_args()
        parser.parse_dirs()
        self.config_settings = parser.parse_config(self.args)
        self.final_settings = parser.parse_args(self.args, self.config_settings)

    def test_parse_dirs(self):
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
        self.assertEqual(amount_general_settings, 17)
        self.assertEqual(amount_library_settings, 9)
        self.assertFalse(general["start_fullscreen"])
        self.assertEqual(general["slideshow_delay"], 2)
        self.assertTrue(general["display_bar"])
        self.assertEqual(library["file_check_amount"], 30)
