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
        vimiv: The main vimiv class to interact with.
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
    """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Default values
        self.hidden = general["display_bar"]
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
        self.bar.add(self.left_label)
        self.bar.add(self.center_label)
        self.bar.add(self.right_label)
        self.bar.set_border_width(10)
        self.bar.set_valign(Gtk.Align.END)

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
            if self.vimiv.library.treeview.is_focus():
                self.left_label.set_text(os.getcwd())
            # Position, name and thumbnail size in thumb mode
            elif self.vimiv.thumbnail.toggled:
                pos = self.vimiv.thumbnail.pos
                for i in self.vimiv.thumbnail.errorpos:
                    if pos >= i:
                        pos += 1
                name = os.path.basename(self.vimiv.paths[pos])
                message = "{0}/{1}  {2}  {3}". \
                    format(self.vimiv.thumbnail.pos + 1,
                           len(self.vimiv.paths) -
                           len(self.vimiv.thumbnail.errorpos),
                           name, self.vimiv.thumbnail.size)
                self.left_label.set_text(message)
            # Image info in image mode
            else:
                name = os.path.basename(self.vimiv.paths[self.vimiv.index])
                message = "{0}/{1}  {2}  [{3:.0f}%]". \
                    format(self.vimiv.index + 1, len(self.vimiv.paths), name,
                           self.vimiv.image.zoom_percent * 100)
                self.left_label.set_text(message)
        except:
            self.left_label.set_text("No open images")
        # Center
        if not (self.vimiv.thumbnail.toggled or
                self.vimiv.library.treeview.is_focus()) and self.vimiv.paths:
            mark = "[*]" if self.vimiv.paths[self.vimiv.index] \
                in self.vimiv.mark.marked else ""
        else:
            mark = ""
        if self.vimiv.slideshow.running:
            slideshow = "[slideshow - {0:.1f}s]".format(
                self.vimiv.slideshow.delay)
        else:
            slideshow = ""
        message = "{0}  {1}".format(mark, slideshow)
        self.center_label.set_text(message)
        # Right side
        mode = self.get_mode()
        message = "{0:15}  {1:4}".format(mode, self.vimiv.keyhandler.num_str)
        self.right_label.set_markup(message)
        # Window title
        try:
            name = os.path.basename(self.vimiv.paths[self.vimiv.index])
            self.vimiv.set_title("vimiv - " + name)
        except:
            self.vimiv.set_title("vimiv")
        # Size of statusbar for resizing image
        self.size = self.vimiv.statusbar.bar.get_allocated_height()

    def get_mode(self):
        """Return which widget is currently focused."""
        if self.vimiv.library.treeview.is_focus():
            return "<b>-- LIBRARY --</b>"
        elif self.vimiv.manipulate.toggled:
            return "<b>-- MANIPULATE --</b>"
        elif self.vimiv.thumbnail.toggled:
            return "<b>-- THUMBNAIL --</b>"
        else:
            return "<b>-- IMAGE --</b>"

    def toggle(self):
        """Toggle statusbar and resize image if necessary."""
        if not self.hidden and not self.vimiv.commandline.entry.is_visible():
            self.bar.hide()
        else:
            self.bar.show()
        self.hidden = not self.hidden
        # Resize the image if necessary
        if not self.vimiv.image.user_zoomed and self.vimiv.paths and \
                not self.vimiv.thumbnail.toggled:
            self.vimiv.image.zoom_to(0)
