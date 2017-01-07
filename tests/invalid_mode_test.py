# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Fail functions because called from wrong mode test for vimiv's test suite."""

from unittest import main
from vimiv_testcase import VimivTestCase


class FailingModeTest(VimivTestCase):
    """Failing Mode Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.cmdline = cls.vimiv["commandline"]
        cls.entry = cls.cmdline.entry

    def test_fail_focus_slider(self):
        """Fail focus slider because not in manipulate."""
        self.vimiv["manipulate"].focus_slider("bri")
        self.assertEqual(
            self.vimiv["statusbar"].left_label.get_text(),
            "ERROR: Focusing a slider only makes sense in manipulate")

    def test_fail_button_clicked(self):
        """Fail exiting manipulate via button_clicked."""
        self.vimiv["manipulate"].button_clicked(None, False)
        self.assertEqual(
            self.vimiv["statusbar"].left_label.get_text(),
            "ERROR: Finishing manipulate only makes sense in manipulate")


if __name__ == '__main__':
    main()
