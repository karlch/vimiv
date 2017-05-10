# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Fail commands because of arguments test for vimiv's test suite."""

from unittest import main

from vimiv_testcase import VimivTestCase


class FailingArgTest(VimivTestCase):
    """Failing Argument Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.cmdline = cls.vimiv["commandline"]
        cls.entry = cls.cmdline.entry

    def test_args(self):
        """Fail commands because of wrong number of arguments."""
        # 0 Arguments allowed
        for cmd in ["accept_changes", "autorotate", "center", "copy_abspath",
                    "copy_basename", "delete", "first", "first_lib", "fit",
                    "fit_horiz", "fit_vert", "focus_library", "fullscreen",
                    "last", "last_lib", "library", "manipulate", "mark",
                    "mark_all", "mark_between", "move_up", "next", "next!",
                    "prev", "prev!", "q", "q!", "reload_lib", "set animation!",
                    "set clipboard!", "set rescale_svg!", "set show_hidden!",
                    "set statusbar!", "slideshow", "thumbnail",
                    "unfocus_library", "version"]:
            self.fail_arguments(cmd, 1, too_many=True)
        # 1 Argument optional
        for cmd in ["grow_lib", "set brightness", "set contrast",
                    "set library_width", "set sharpness", "set slideshow_delay",
                    "shrink_lib", "zoom_in", "zoom_out", "zoom_to",
                    "set overzoom"]:
            self.fail_arguments(cmd, 2, too_many=True)
        # 1 Argument required
        for cmd in ["flip", "format", "rotate", "slideshow_delay", "tag_write",
                    "tag_load", "tag_remove", "undelete"]:
            self.fail_arguments(cmd, 2, too_many=True)
            self.fail_arguments(cmd, 0, too_many=False)
        # 2 Arguments required
        for cmd in ["alias"]:
            self.fail_arguments(cmd, 3, too_many=True)
            self.fail_arguments(cmd, 1, too_many=False)

    def fail_arguments(self, command, n_args, too_many=True):
        """Fail a command because of too many or too few arguments.

        Check for the correct error message.

        args:
            command: Command to fail.
            n_args: Amount of arguments to try.
            too_many: If True, n_args are too many for command. Otherwise too
                few.
        """
        text = ":" + command + " arg" * n_args
        self.entry.set_text(text)
        self.cmdline.handler(self.entry)
        expected = "ERROR: Too many arguments for command" \
            if too_many \
            else "ERROR: Missing positional arguments for command"
        self.assertIn(expected, self.vimiv["statusbar"].left_label.get_text())


if __name__ == "__main__":
    main()
