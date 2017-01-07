#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Statusbar for vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk


class Statusbar(object):
    """Create the statusbar and handle all events for it.

    Attributes:
        app: The main vimiv application to interact with.
        hidden: If True the statusbar is not visible.
        errors: True if there are errors.
        search_names: List of names of the search results.
        search_positions: List of positions of the search results.
        timer_id: ID of the currently running GLib.Timeout.
        size: Height of the statusbar.
        lock: If True do not update any information.
        was_hidden: If True the statusbar was hidden before an error message.
        bar: Gtk.Grid containing all widgets.
        left_label: Gtk.Label containing position, name and zoom.
        right_label: Gtk.Label containing mode and prefixed numbers.
        center_label: Gtk.Label containing mark status and slideshow info.
        separator: Gtk.Separator used as background of the statusbar. Makes sure
            the other widgets do not interfere with the overlaying bar.
    """

    def __init__(self, app, settings):
        self.app = app
        general = settings["GENERAL"]

        # Default values
        self.hidden = not general["display_bar"]
        self.errors = True
        self.search_names = []
        self.search_positions = []
        self.timer_id = 0
        self.size = 0
        self.lock = False
        self.was_hidden = False

        # Statusbar on the bottom
        self.bar = Gtk.Grid()
        self.bar.set_name("StatusBar")  # Name for css
        # Two labels for two sides of statusbar and one in the middle for
        # additional info
        self.left_label = Gtk.Label()
        self.left_label.set_justify(Gtk.Justification.LEFT)
        self.right_label = Gtk.Label()
        self.right_label.set_justify(Gtk.Justification.RIGHT)
        self.center_label = Gtk.Label()
        self.center_label.set_justify(Gtk.Justification.CENTER)
        self.center_label.set_hexpand(True)
        # Add them all
        self.bar.attach(self.left_label, 0, 0, 1, 1)
        self.bar.attach(self.center_label, 1, 0, 1, 1)
        self.bar.attach(self.right_label, 2, 0, 1, 1)
        # Padding and separator
        padding = self.app.settings["GENERAL"]["commandline_padding"]
        self.bar.set_margin_start(padding)
        self.bar.set_margin_end(padding)
        self.bar.set_margin_top(padding)
        self.bar.set_margin_bottom(padding)
        self.separator = Gtk.Separator()

    def message(self, message, style="error"):
        """Push a message to the statusbar.

        Args:
            message: Message to push.
            style: One of error, warning and info.
        """
        if self.app.debug:
            self.app["log"].write_message(style, message)
        self.errors = True
        styles = {"error": "#CC0000", "warning": "#FA9E21", "info": "#6699FF"}
        message = "<b><span foreground='" + styles[style] + "'>" + \
            style.upper() + ": </span></b>" + message
        self.timer_id = GLib.timeout_add_seconds(5, self.update_info)
        # Show if is was hidden
        if self.hidden:
            self.toggle()
            self.was_hidden = True
        self.left_label.set_markup(message)
        # CSS to style bar according to message
        css_provider = Gtk.CssProvider()
        css_str = "#OverLay { border-top: solid 2px " + styles[style] + ";}"
        css_provider.load_from_data(css_str.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def error_false(self):
        """Strip one error and update the statusbar if no more errors remain."""
        # Remove any timers that remove the error message
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = 0
        # Strip one error
        self.errors = False
        # Reset css from error_message
        css_provider = Gtk.CssProvider()
        css_str = "#OverLay { border-top: solid 0px; }"
        css_provider.load_from_data(css_str.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def update_info(self):
        """Update the statusbar and the window title."""
        # Return if it is locked
        if self.lock:
            return
        # Hide again if it was shown due to an error message
        if self.was_hidden:
            self.was_hidden = False
            self.toggle()
        # Strip error messages if any
        if self.errors:
            self.error_false()
        # Get mode first
        mode = self.get_mode()
        # Update all relevant widgets
        self.set_left_status(mode)
        self.set_center_status(mode)
        self.set_right_status(mode)
        self.set_window_title()
        # Size of statusbar for resizing image
        self.size = self.app["statusbar"].bar.get_allocated_height()

    def set_left_status(self, mode):
        """Set the left side of the statusbar depending on mode."""
        # Directory if library is focused
        if "LIBRARY" in mode:
            cur_dir = os.getcwd()
            if self.app["library"].tilde_in_statusbar:
                cur_dir = cur_dir.replace(os.environ["HOME"], "~")
            self.left_label.set_text(cur_dir)
        # Position, name and thumbnail size in thumb mode
        elif "THUMBNAIL" in mode:
            pos = self.app.get_pos()
            name = os.path.basename(self.app.get_pos(True))
            message = "{0}/{1}  {2}  {3}".format(pos + 1,
                                                 len(self.app.paths),
                                                 name,
                                                 self.app["thumbnail"].size)
            self.left_label.set_text(message)
        # In commandline
        elif "COMMAND" in mode:
            # TODO useful information in the commandline
            self.left_label.set_text("")
        elif self.app.paths:
            name = os.path.basename(self.app.paths[self.app.index])
            message = "{0}/{1}  {2}  [{3:.0f}%]".format(
                self.app.index + 1, len(self.app.paths), name,
                self.app["image"].zoom_percent * 100)
            self.left_label.set_text(message)
        else:
            self.left_label.set_text("No open images")

    def set_center_status(self, mode):
        """Set the centre of the statusbar depending on mode."""
        mark = "[*]" \
            if ("IMAGE" in mode or "MANIPULATE" in mode) \
            and self.app.paths \
            and self.app.paths[self.app.index] in self.app["mark"].marked \
            else ""
        slideshow = \
            "[slideshow - {0:.1f}s]".format(self.app["slideshow"].delay) \
            if self.app["slideshow"].running else ""
        message = "{0}  {1}".format(mark, slideshow)
        self.center_label.set_text(message)

    def set_right_status(self, mode):
        """Set the right side of the statusbar to mode and num_str."""
        message = "{0:15}  {1:4}".format(mode, self.app["keyhandler"].num_str)
        self.right_label.set_markup(message)

    def set_window_title(self):
        """Set window title depending on whether there are valid paths."""
        if self.app.paths:
            name = os.path.basename(self.app.paths[self.app.index])
            self.app["window"].set_title("vimiv - " + name)
        else:
            self.app["window"].set_title("vimiv")

    def get_mode(self):
        """Return which widget is currently focused."""
        if self.app["commandline"].entry.is_focus():
            return "<b>-- COMMAND --</b>"
        elif self.app["library"].treeview.is_focus():
            return "<b>-- LIBRARY --</b>"
        elif self.app["manipulate"].scrolled_win.is_visible():
            return "<b>-- MANIPULATE --</b>"
        elif self.app["thumbnail"].toggled:
            return "<b>-- THUMBNAIL --</b>"
        else:
            return "<b>-- IMAGE --</b>"

    def toggle(self):
        """Toggle statusbar and resize image if necessary."""
        if not self.hidden and not self.app["commandline"].entry.is_visible():
            self.bar.hide()
            self.separator.hide()
        else:
            self.bar.show()
            self.separator.show()
        self.hidden = not self.hidden
        # Resize the image if necessary
        if self.app["image"].fit_image and self.app.paths and \
                not self.app["thumbnail"].toggled and \
                not self.app["image"].is_anim:
            self.app["image"].zoom_to(0, self.app["image"].fit_image)

    def set_separator_height(self):
        """Set height of the separator used as background of the statusbar."""
        bar_height = self.bar.get_allocated_height()
        padding = self.app.settings["GENERAL"]["commandline_padding"]
        separator_height = bar_height + 2 * padding
        self.separator.set_margin_top(separator_height)

    def clear_status(self):
        """Clear num_str, search and error messages from the statusbar."""
        self.app["commandline"].reset_search(leaving=False)
        self.app["keyhandler"].num_clear()
