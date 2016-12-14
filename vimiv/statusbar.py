#!/usr/bin/env python
# encoding: utf-8
"""Statusbar for vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk


class Statusbar(object):
    """Create the statusbar and handle all events for it.

    Attributes:
        app: The main vimiv application to interact with.
        hidden: If True the statusbar is not visible.
        errors: List of errors.
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
        self.errors = []
        self.search_names = []
        self.search_positions = []
        self.timer_id = GLib.Timeout
        self.size = 0
        self.lock = False
        self.was_hidden = False

        # Statusbar on the bottom
        self.bar = Gtk.Grid()
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
        self.bar.set_margin_left(padding)
        self.bar.set_margin_right(padding)
        self.bar.set_margin_top(padding)
        self.bar.set_margin_bottom(padding)
        self.separator = Gtk.Separator()

    def err_message(self, message):
        """Push an error message to the statusbar.

        Args:
            message: Message to push.
        """
        self.errors.append(1)
        message = "<b>" + message + "</b>"
        self.timer_id = GLib.timeout_add_seconds(5, self.error_false)
        # Show if is was hidden
        if self.hidden:
            self.toggle()
            self.was_hidden = True
        self.left_label.set_markup(message)

    def error_false(self):
        """Strip one error and update the statusbar if no more errors remain."""
        self.errors = self.errors[0:-1]
        if not self.errors:
            self.update_info()

    def update_info(self):
        """Update the statusbar and the window title."""
        # Return if it is locked
        if self.lock:
            return
        # Hide again if it was shown due to an error message
        if self.was_hidden:
            self.was_hidden = False
            self.toggle()
        # Left side
        try:
            # Directory if library is focused
            if self.app["library"].treeview.is_focus():
                self.left_label.set_text(os.getcwd())
            # Position, name and thumbnail size in thumb mode
            elif self.app["thumbnail"].toggled:
                pos = self.app.get_pos()
                name = os.path.basename(self.app.paths[pos])
                message = "{0}/{1}  {2}  {3}". \
                    format(pos + 1, len(self.app.paths),
                           name, self.app["thumbnail"].size)
                self.left_label.set_text(message)
            # Image info in image mode
            else:
                name = os.path.basename(self.app.paths[self.app.index])
                message = "{0}/{1}  {2}  [{3:.0f}%]". \
                    format(self.app.index + 1, len(self.app.paths), name,
                           self.app["image"].zoom_percent * 100)
                self.left_label.set_text(message)
        except:
            self.left_label.set_text("No open images")
        # Center
        if not (self.app["thumbnail"].toggled or
                self.app["library"].treeview.is_focus()) and self.app.paths:
            mark = "[*]" if self.app.paths[self.app.index] \
                in self.app["mark"].marked else ""
        else:
            mark = ""
        if self.app["slideshow"].running:
            slideshow = "[slideshow - {0:.1f}s]".format(
                self.app["slideshow"].delay)
        else:
            slideshow = ""
        message = "{0}  {1}".format(mark, slideshow)
        self.center_label.set_text(message)
        # Right side
        mode = self.get_mode()
        message = "{0:15}  {1:4}".format(mode, self.app["keyhandler"].num_str)
        self.right_label.set_markup(message)
        # Window title
        try:
            name = os.path.basename(self.app.paths[self.app.index])
            self.app["window"].set_title("vimiv - " + name)
        except:
            self.app["window"].set_title("vimiv")
        # Size of statusbar for resizing image
        self.size = self.app["statusbar"].bar.get_allocated_height()

    def get_mode(self):
        """Return which widget is currently focused."""
        if self.app["library"].treeview.is_focus():
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
        if not self.app["image"].user_zoomed and self.app.paths and \
                not self.app["thumbnail"].toggled:
            self.app["image"].zoom_to(0)

    def set_separator_height(self):
        """Set height of the separator used as background of the statusbar."""
        bar_height = self.bar.get_allocated_height()
        padding = self.app.settings["GENERAL"]["commandline_padding"]
        separator_height = bar_height + 2 * padding
        self.separator.set_margin_top(separator_height)
