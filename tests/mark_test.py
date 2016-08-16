#!/usr/bin/env python
# encoding: utf-8
""" Mark tests for vimiv's test suite """

import os
from unittest import TestCase, main
from vimiv.fileactions import populate
import vimiv.main as v_main
from vimiv.parser import parse_config


class MarkTest(TestCase):
    """ Mark Tests """

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        os.chdir("vimiv")
        cls.settings = parse_config()
        paths, index = populate(["testimages"], False, False)
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.vimiv.main(True)
        # Move away from directory
        cls.vimiv.library.scroll("j")

    def test_mark(self):
        """ Marking images """
        # Mark
        self.vimiv.mark.mark()
        expected_marked = [os.path.abspath("arch_001.jpg")]
        self.assertEqual(expected_marked, self.vimiv.mark.marked)
        # Remove mark
        self.vimiv.mark.mark()
        self.assertEqual([], self.vimiv.mark.marked)

    def test_toggle_mark(self):
        """ Toggle marks """
        self.vimiv.mark.mark()
        self.vimiv.mark.toggle_mark()
        self.assertEqual([], self.vimiv.mark.marked)
        self.vimiv.mark.toggle_mark()
        expected_marked = [os.path.abspath("arch_001.jpg")]
        self.assertEqual(expected_marked, self.vimiv.mark.marked)

    def test_mark_all(self):
        """ Mark all """
        self.vimiv.mark.mark_all()
        expected_marked = ["arch_001.jpg", "arch-logo.png", "symlink_to_image",
                           "vimiv.bmp", "vimiv.svg", "vimiv.tiff"]
        expected_marked = [os.path.abspath(image) for image in expected_marked]
        self.assertEqual(expected_marked, self.vimiv.mark.marked)

    def test_mark_between(self):
        """ Mark between """
        self.vimiv.mark.mark()
        self.vimiv.keyhandler.num_str = "3"
        self.vimiv.library.scroll("j")
        self.vimiv.mark.mark()
        self.vimiv.mark.mark_between()
        expected_marked = ["arch_001.jpg", "arch-logo.png", "symlink_to_image"]
        expected_marked = [os.path.abspath(image) for image in expected_marked]
        self.assertEqual(expected_marked, self.vimiv.mark.marked)

    def tearDown(self):
        self.vimiv.mark.marked = []
        self.vimiv.library.move_pos(False)
        self.vimiv.library.scroll("j")

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
