#!/usr/bin/env python
# encoding: utf-8
""" Tests the main part of vimiv by simply running through it.
    All parts are tested by themselves anyway, this just checks if they run
    together without errors. """

from unittest import TestCase, main
import vimiv.main as v_main


class MainTest(TestCase):
    """ Main Test Class """

    def test_main_until_quit(self):
        """ Run through vimiv main once """
        v_main.main(True)

if __name__ == '__main__':
    main()
