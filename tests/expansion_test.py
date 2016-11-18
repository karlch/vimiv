#!/usr/bin/env python
# encoding: utf-8
"""Expansion of % and * tests for vimiv's test suite."""


from unittest import TestCase, main
import vimiv.main as v_main
from vimiv.parser import parse_config
from vimiv.fileactions import populate


class CommandlineTest(TestCase):
    """Command Line Tests."""

    @classmethod
    def setUpClass(cls):
        paths, index = populate(["vimiv/testimages/arch_001.jpg"], False, False)
        cls.settings = parse_config()
        cls.vimiv = v_main.Vimiv(cls.settings, paths, index)
        cls.vimiv.main()

    def test_expansion(self):
        """Expanding % and * in different modes."""
        # Image
        self.vimiv.window.last_focused = "im"
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv.paths)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)

        # Library
        self.vimiv.window.last_focused = "lib"
        self.vimiv.library.focus()
        self.vimiv.library.scroll("j")
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv.library.files)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)
        print("\t\t", self.vimiv.get_pos(True))

        # Thumbnail
        self.vimiv.thumbnail.toggle()
        self.vimiv.thumbnail.move_direction("l")
        self.vimiv.window.last_focused = "thu"
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv.paths)
        received_cmd = self.vimiv.commandline.expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)

if __name__ == '__main__':
    main()
