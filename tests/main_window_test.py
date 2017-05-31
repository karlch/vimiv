# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test the MainWindow for vimiv's testsuite."""

from unittest import main

from vimiv_testcase import VimivTestCase, refresh_gui


class MainWindowTest(VimivTestCase):
    """MainWindow Test."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch_001.jpg"])
        cls.window = cls.vimiv["main_window"]

    def test_scroll(self):
        """Scroll an image."""
        def there_and_back(there, back):
            """Scroll in direction and back to the beginning.

            Args:
                there: Direction to scroll in.
                back: Direction to scroll back in.
            Return:
                Position after scrolling.
            """
            if there in "lL":
                adj = self.window.get_hadjustment()
            else:
                adj = self.window.get_vadjustment()
            self.window.scroll(there)
            new_pos = adj.get_value()
            self.assertGreater(adj.get_value(), 0)
            self.window.scroll(back)
            self.assertFalse(adj.get_value())
            return new_pos
        refresh_gui()
        # First zoom so something can happen
        size = self.window.get_allocation()
        w_scale = \
            size.width / self.vimiv["image"].get_pixbuf_original().get_width()
        h_scale = \
            size.height / self.vimiv["image"].get_pixbuf_original().get_height()
        needed_scale = max(w_scale, h_scale) * 1.5
        self.vimiv["image"].zoom_to(needed_scale)
        refresh_gui()
        # Adjustments should be at 0
        h_adj = self.window.get_hadjustment()
        v_adj = self.window.get_vadjustment()
        self.assertFalse(h_adj.get_value())
        self.assertFalse(v_adj.get_value())
        # Right and back left
        there_and_back("l", "h")
        # Down and back up
        there_and_back("j", "k")
        # Far right and back
        right_end = there_and_back("L", "H")
        self.assertEqual(
            right_end,
            h_adj.get_upper() - h_adj.get_lower() - size.width)
        # Bottom and back
        bottom = there_and_back("J", "K")
        self.assertEqual(
            bottom,
            v_adj.get_upper() - v_adj.get_lower() - size.height)
        # Center
        self.window.center_window()
        h_adj = self.window.get_hadjustment()
        v_adj = self.window.get_vadjustment()
        h_middle = \
            (h_adj.get_upper() - h_adj.get_lower() - size.width) / 2
        v_middle = \
            (v_adj.get_upper() - v_adj.get_lower() - size.height) / 2
        self.assertEqual(h_adj.get_value(), h_middle)
        self.assertEqual(v_adj.get_value(), v_middle)

    def test_scroll_error(self):
        """Scroll image or thumbnail with invalid argument."""
        # Error message
        self.window.scroll("m")
        self.check_statusbar("ERROR: Invalid scroll direction m")


if __name__ == "__main__":
    main()
