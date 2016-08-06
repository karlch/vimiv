#!/usr/bin/env python
# encoding: utf-8
""" Test slideshow.py for vimiv's test suite """

import os
import time
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.parser import parse_config
from vimiv.fileactions import populate


def refresh_gui(delay=0):
    """ Refresh the Gtk window as the Gtk.main() loop is not running when
        testing """
    time.sleep(delay)
    Gtk.main_iteration_do(False)


class SlideshowTest(TestCase):
    """ Slideshow Tests """

    @classmethod
    def setUpClass(cls):
        cls.working_directory = os.getcwd()
        cls.settings = parse_config()
        paths, index = populate(["testimages/arch_001.jpg"])
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.slideshow = cls.vimiv.slideshow
        cls.vimiv.main(True)

    def test_toggle(self):
        """ Toggle slideshow """
        self.assertFalse(self.slideshow.running)
        self.slideshow.toggle()
        self.assertTrue(self.slideshow.running)
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        # Throw some errors
        self.vimiv.thumbnail.toggled = True
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv.thumbnail.toggled = False
        paths_before = self.vimiv.paths
        self.vimiv.paths = []
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv.paths = paths_before

    def test_set_delay(self):
        """ Set slideshow delay """
        self.assertEqual(self.slideshow.delay, 2.0)
        self.slideshow.set_delay(3.0)
        self.assertEqual(self.slideshow.delay, 3.0)
        self.slideshow.set_delay(None, "-")
        self.assertEqual(self.slideshow.delay, 2.8)
        self.slideshow.set_delay(None, "+")
        self.assertEqual(self.slideshow.delay, 3.0)
        # Set via toggle
        self.vimiv.keyhandler.num_str = "2"
        self.slideshow.toggle()
        self.assertEqual(self.slideshow.delay, 2.0)

    def test_running(self):
        """ Check if slideshow runs correctly """
        self.assertEqual(self.vimiv.index, 0)
        self.slideshow.toggle()
        # Set delay when running
        self.slideshow.set_delay(0.001)
        refresh_gui()
        self.assertEqual(self.vimiv.slideshow.delay, 0.001)
        refresh_gui(0.001)
        self.assertEqual(self.vimiv.index, 1)
        refresh_gui()
        self.assertEqual(self.vimiv.index, 2)
        refresh_gui()
        self.assertEqual(self.vimiv.index, 0)

    def tearDown(self):
        if self.slideshow.running:
            self.slideshow.toggle()
        self.slideshow.delay = 2.0

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
