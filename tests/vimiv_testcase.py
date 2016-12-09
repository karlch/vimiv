#!/usr/bin/env python
# encoding: utf-8
"""Wrapper of TestCase which sets up the vimiv class and quits it when done."""

import os
from time import time
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
import vimiv.main as v_main
from vimiv.parser import parse_config


class VimivTestCase(TestCase):
    """Wrapper Class of TestCase."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def init_test(self, settings={}, paths=[], index=0, arguments=[]):
        """Initialize a testable vimiv object saved as self.vimiv.

        Args:
            settings: Settings passed to vimiv.
            paths: Paths passed to vimiv.
            index: Index in paths.
            arguments: Commandline arguments for vimiv.
        """
        # A new ID for every generated vimiv class
        vimiv_id = "org.vimiv" + str(time()).replace(".", "")
        # Create vimiv class with settings, paths, ...
        self.vimiv = v_main.main(arguments, vimiv_id)
        if not settings:
            settings = parse_config()
        self.vimiv.set_settings(settings)
        self.vimiv.set_paths(paths, index)
        self.working_directory = os.getcwd()
        # Start vimiv without running the main loop
        self.vimiv.register()
        self.vimiv.do_startup(self.vimiv)
        self.vimiv.activate(self.vimiv)

    @classmethod
    def tearDownClass(cls):
        cls.vimiv.quit()
        os.chdir(cls.working_directory)


if __name__ == '__main__':
    main()
