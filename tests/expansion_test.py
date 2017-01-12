# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Expansion of % and * tests for vimiv's test suite."""

from unittest import main

from vimiv_testcase import VimivTestCase


class ExpansionTest(VimivTestCase):
    """Expansion Tests."""

    @classmethod
    def setUpClass(cls):
        paths = ["vimiv/testimages/arch_001.jpg"]
        cls.init_test(cls, paths)

    def test_expansion(self):
        """Expanding % and * in different modes."""
        # Image
        self.vimiv["commandline"].last_focused = "im"
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv.paths)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)

        # Library
        self.vimiv["commandline"].last_focused = "lib"
        self.vimiv["library"].focus()
        self.vimiv["library"].scroll("j")
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv["library"].files)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)

        # Thumbnail
        self.vimiv["thumbnail"].toggle()
        self.vimiv["thumbnail"].move_direction("l")
        self.vimiv["commandline"].last_focused = "thu"
        expected_cmd = "!echo " + self.vimiv.get_pos(True)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo %")
        self.assertEqual(expected_cmd, received_cmd)
        expected_cmd = "!echo " + " ".join(self.vimiv.paths)
        received_cmd = self.vimiv["commandline"].expand_filenames(":!echo *")
        self.assertEqual(expected_cmd, received_cmd)


if __name__ == "__main__":
    main()
