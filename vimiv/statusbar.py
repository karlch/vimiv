# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Statusbar for vimiv."""

import os

from gi.repository import Gdk, GLib, Gtk


class Statusbar(Gtk.Grid):
    """Create the statusbar and handle all events for it.

    Attributes:
        hidden: If True, the statusbar is not visible.
        size: Height of the statusbar.
        lock: If True, do not update any information.
        separator: Gtk.Separator used as background of the statusbar. Makes sure
            the other widgets do not interfere with the overlaying bar.

        _app: The main vimiv application to interact with.
        _center_label: Gtk.Label containing mark status and slideshow info.
        _errors: True if there are errors.
        _left_label: Gtk.Label containing position, name and zoom.
        _right_label: Gtk.Label containing mode and prefixed numbers.
        _tilde_in_statusbar: If True, collapse $HOME to ~ in library statusbar.
        _timer_id: ID of the currently running GLib.Timeout.
        _was_hidden: If True the statusbar was hidden before an error message.
    """

    def __init__(self, app, settings):
        super(Statusbar, self).__init__()
        self._app = app
        general = settings["GENERAL"]

        # Default values
        self.hidden = not general["display_bar"]
        self.lock = False
        self._errors = True
        self._tilde_in_statusbar = settings["LIBRARY"]["tilde_in_statusbar"]
        self._timer_id = 0
        self._was_hidden = False

        # Statusbar on the bottom
        self.set_name("StatusBar")  # Name for css
        # Two labels for two sides of statusbar and one in the middle for
        # additional info
        self._left_label = Gtk.Label()
        self._left_label.set_justify(Gtk.Justification.LEFT)
        self._right_label = Gtk.Label()
        self._right_label.set_justify(Gtk.Justification.RIGHT)
        self._center_label = Gtk.Label()
        self._center_label.set_justify(Gtk.Justification.CENTER)
        self._center_label.set_hexpand(True)
        # Add them all
        self.attach(self._left_label, 0, 0, 1, 1)
        self.attach(self._center_label, 1, 0, 1, 1)
        self.attach(self._right_label, 2, 0, 1, 1)
        # Padding and separator
        padding = self._app.settings["GENERAL"]["commandline_padding"]
        self.set_margin_start(padding)
        self.set_margin_end(padding)
        self.set_margin_top(padding)
        self.set_margin_bottom(padding)
        self.separator = Gtk.Separator()

        # Connect signals
        self._app["commandline"].search.connect("no-search-results",
                                                self._on_no_search_results)

    def message(self, message, style="error", timeout=5):
        """Push a message to the statusbar.

        Args:
            message: Message to push.
            style: One of error, warning and info.
            timeout: Time until the message shall be removed by update info.
        """
        if self._app.debug:
            self._app["log"].write_message(style, message)
        self._errors = True
        styles = {"error": "#CC0000", "warning": "#FA9E21", "info": "#6699FF"}
        message = "<b><span foreground='" + styles[style] + "'>" + \
            style.upper() + ": </span></b>" + message
        self._timer_id = GLib.timeout_add(timeout * 1000, self.update_info)
        # Show if is was hidden
        if self.hidden:
            self.toggle()
            self._was_hidden = True
        self._left_label.set_markup(message)
        # CSS to style bar according to message
        css_provider = Gtk.CssProvider()
        css_str = "#OverLay { border-top: solid 2px " + styles[style] + ";}"
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
        if self._was_hidden:
            self._was_hidden = False
            self.toggle()
        # Strip error messages if any
        if self._errors:
            self._error_false()
        # Get mode first
        mode = self._get_mode()
        # Update all relevant widgets
        self._set_left_status(mode)
        self._set_center_status(mode)
        self._set_right_status(mode)
        self._set_window_title()

    def _error_false(self):
        """Strip one error and update the statusbar if no more errors remain."""
        # Remove any timers that remove the error message
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0
        # Strip one error
        self._errors = False
        # Reset css from error_message
        css_provider = Gtk.CssProvider()
        css_str = "#OverLay { border-top: solid 0px; }"
        css_provider.load_from_data(css_str.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _set_left_status(self, mode):
        """Set the left side of the statusbar depending on mode."""
        # Directory if library is focused
        if "LIBRARY" in mode:
            cur_dir = os.getcwd()
            if self._tilde_in_statusbar:
                cur_dir = cur_dir.replace(os.getenv("HOME"), "~")
            self._left_label.set_text(cur_dir)
        # Position, name and thumbnail size in thumb mode
        elif "THUMBNAIL" in mode:
            pos = self._app.get_pos()
            name = os.path.basename(self._app.get_pos(True))
            message = "{0}/{1}  {2}  {3}".format(
                pos + 1, len(self._app.get_paths()), name,
                self._app["thumbnail"].get_zoom_level())

            self._left_label.set_text(message)
        # In commandline
        elif "COMMAND" in mode:
            # TODO useful information in the commandline
            self._left_label.set_text("")
        elif self._app.get_paths():
            name = os.path.basename(self._app.get_path())
            message = "{0}/{1}  {2}  [{3:.0f}%]".format(
                self._app.get_index() + 1, len(self._app.get_paths()), name,
                self._app["image"].zoom_percent * 100)
            self._left_label.set_text(message)
        else:
            self._left_label.set_text("No open images")

    def _set_center_status(self, mode):
        """Set the centre of the statusbar depending on mode."""
        mark = "[*]" \
            if ("IMAGE" in mode or "MANIPULATE" in mode) \
            and self._app.get_paths() \
            and self._app.get_path() in self._app["mark"].marked \
            else ""
        slideshow = self._app["slideshow"].get_formatted_delay() \
            if self._app["slideshow"].running else ""
        message = "{0}  {1}".format(mark, slideshow)
        self._center_label.set_text(message)

    def _set_right_status(self, mode):
        """Set the right side of the statusbar to mode and num_str."""
        message = "{0:15}  {1:4}".format(mode,
                                         self._app["eventhandler"].num_str)
        self._right_label.set_markup(message)

    def _set_window_title(self):
        """Set window title depending on whether there are valid paths."""
        if self._app.get_paths():
            name = os.path.basename(self._app.get_path())
            self._app["window"].set_title("vimiv - " + name)
        else:
            self._app["window"].set_title("vimiv")

    def _get_mode(self):
        """Return which widget is currently focused."""
        if self._app["commandline"].is_focus():
            return "<b>-- COMMAND --</b>"
        elif self._app["library"].is_focus():
            return "<b>-- LIBRARY --</b>"
        elif self._app["manipulate"].is_visible():
            return "<b>-- MANIPULATE --</b>"
        elif self._app["thumbnail"].toggled:
            return "<b>-- THUMBNAIL --</b>"
        return "<b>-- IMAGE --</b>"

    def toggle(self):
        """Toggle statusbar and resize image if necessary."""
        if not self.hidden and not self._app["commandline"].is_visible():
            self.hide()
            self.separator.hide()
        else:
            self.show()
            self.separator.show()
        self.hidden = not self.hidden
        self._app.emit("widget-layout-changed", self)

    def clear_status(self):
        """Clear num_str, search and error messages from the statusbar."""
        self._app["commandline"].search.reset()
        self._app["eventhandler"].num_clear()

    def set_separator_height(self):
        """Set height of the separator used as background of the statusbar."""
        self.separator.set_size_request(1, self.get_bar_height())

    def get_bar_height(self):
        """Return height of the statusbar + padding."""
        bar_height = self.get_allocated_height()
        padding = self._app.settings["GENERAL"]["commandline_padding"]
        return bar_height + 2 * padding

    def get_message(self):
        return self._left_label.get_text()

    def _on_no_search_results(self, search, searchstr):
        self.message('No file matching "%s"' % (searchstr), "info")
