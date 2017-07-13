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

    def test_args(self):
        """Fail commands because of wrong number of arguments."""
        # 0 Arguments allowed
        for cmd in ["accept_changes", "autorotate", "center", "copy_abspath",
                    "copy_basename", "delete", "first", "first_lib", "fit",
                    "fit_horiz", "fit_vert", "focus_library", "fullscreen",
                    "last", "last_lib", "library", "manipulate", "mark",
                    "mark_all", "mark_between", "move_up", "next", "next!",
                    "prev", "prev!", "q", "q!", "reload_lib", "slideshow",
                    "thumbnail", "unfocus_library", "version", "w", "wq"]:
            self.fail_arguments(cmd, 1, too_many=True)
        # 1 Argument optional
        for cmd in ["zoom_in", "zoom_out", "zoom_to"]:
            self.fail_arguments(cmd, 2, too_many=True)
        # 1 Argument required
        for cmd in ["flip", "rotate"]:
            self.fail_arguments(cmd, 2, too_many=True)
            self.fail_arguments(cmd, 0, too_many=False)
        # 1 Argument required, 1 argument optional
        for cmd in ["edit", "set"]:
            self.fail_arguments(cmd, 3, too_many=True)
            self.fail_arguments(cmd, 0, too_many=False)
        # 1 Argument required, any amount possible
        for cmd in ["format", "tag_write", "tag_load", "tag_remove",
                    "undelete"]:
            self.fail_arguments(cmd, 0, too_many=False)
            self.allow_arbitary_n_arguments(cmd, 1)
        # 2 Arguments required, any amount possible
        for cmd in ["alias"]:
            self.fail_arguments(cmd, 1, too_many=False)
            self.allow_arbitary_n_arguments(cmd, 1)

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
        self.cmdline.set_text(text)
        self.cmdline.emit("activate")
        expected = "ERROR: Too many arguments for command" \
            if too_many \
            else "ERROR: Missing positional arguments for command"
        self.assertIn(expected, self.vimiv["statusbar"].get_message())

    def allow_arbitary_n_arguments(self, command, min_n):
        """Fail if the command does not allow an arbitrary amount of arguments.

        Args:
            min_n: Minimum amount of arguments needed.
        """
        for i in range(min_n, min_n * 100, 33):
            command = command + " a" * i
            self.run_command(command)
            not_expected = "ERROR: Too many arguments for command"
            self.assertNotIn(not_expected,
                             self.vimiv["statusbar"].get_message())


if __name__ == "__main__":
    main()
