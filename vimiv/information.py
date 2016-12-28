#!/usr/bin/env python
# encoding: utf-8
"""Information pop-up for vimiv.

Shows the current version, the icon, gives a link to the GitHub site and the
possibility to display the licence.
"""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class Information():
    """Class containing information on vimiv."""

    def __init__(self):
        self.version = "vimiv 0.8.dev0"

    def get_version(self):
        """Return current version.

        Return:
            String of the current version.
        """
        return self.version

    def show_version_info(self, running_tests=False):
        """Show information about current version in a Gtk pop-up.

        Args:
            running_tests: If True running from testsuite. Do not show pop-up.
        """
        # Popup with buttons
        popup = Gtk.Dialog(title="vimiv - Info", transient_for=Gtk.Window())
        licence_button = popup.add_button(" Licence", Gtk.ResponseType.HELP)
        popup.add_button("Close", Gtk.ResponseType.CLOSE)
        # Different widgets
        licence_button.connect("clicked", self.show_licence)
        licence_icon = Gtk.Image.new_from_icon_name(
            "text-x-generic-symbolic", 0)
        licence_button.set_image(licence_icon)
        licence_button.set_always_show_image(True)

        version_label = Gtk.Label()
        version_size = '<span size="x-large">'
        version_label.set_markup(version_size + self.version + '</span>')

        info_label = Gtk.Label()
        info_label.set_text("vimiv - an image viewer with vim-like keybindings")
        info_label.set_hexpand(True)

        website_label = Gtk.Label()
        website_label.set_markup('<a href="https://www.github.com/karlch/vimiv"'
                                 'title="GitHub site">vimiv on GitHub</a>')

        icon_theme = Gtk.IconTheme.get_default()
        # Icon not available in theme when icon cache was not updated
        try:
            vimiv_pixbuf = icon_theme.load_icon("vimiv", 128, 0)
            vimiv_image = Gtk.Image.new_from_pixbuf(vimiv_pixbuf)
            load_image = 1
        except GLib.Error:
            load_image = 0

        # Layout
        box = popup.get_child()
        box.set_border_width(12)
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        box.pack_start(grid, False, False, 12)
        if load_image:
            grid.attach(vimiv_image, 0, 0, 1, 1)
        grid.attach(version_label, 0, 1, 1, 1)
        grid.attach(info_label, 0, 2, 1, 1)
        grid.attach(website_label, 0, 4, 1, 1)
        popup.show_all()
        if not running_tests:
            popup.run()
            popup.destroy()

    def show_licence(self, button, running_tests=False):
        """Show the licence in a new pop-up window.

        Args:
            button: The Gtk.Button() that called this function.
            running_tests: If True running from testsuite. Do not show pop-up.
        """
        popup = Gtk.Dialog(title="vimiv - Licence", transient_for=Gtk.Window())
        popup.add_button("Close", Gtk.ResponseType.CLOSE)

        label = Gtk.Label()
        title = '<span size="large"><b>MIT Licence</b></span>\n\n'

        # Get license text from file
        with open("/usr/share/licenses/vimiv/LICENSE") as license_file:
            license_text = license_file.read()
        label_markup = title + license_text
        label.set_markup(label_markup)

        box = popup.get_child()
        box.pack_start(label, False, False, 0)
        box.set_border_width(12)
        popup.show_all()
        if not running_tests:
            popup.run()
            popup.destroy()
