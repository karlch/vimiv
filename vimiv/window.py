#!/usr/bin/env python
# encoding: utf-8
"""Window class for vimiv."""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv.helpers import scrolltypes


class Window(Gtk.ApplicationWindow):
    """"Vimiv Window containing the general structure.

    Additionally handles events like fullscreen and resize.

    Attributes:
        app: The main vimiv application to interact with.
        fullscreen: If True, the window is displayed fullscreen.
        winsize: The windowsize as tuple.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        Gtk.ApplicationWindow.__init__(self)

        self.app = app
        self.is_fullscreen = False

        # Configurations from vimivrc
        general = settings["GENERAL"]
        start_fullscreen = general["start_fullscreen"]

        self.connect('destroy', self.app.quit_wrapper)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        # Set initial window size
        try:
            winsize = general["geometry"].split("x")
            self.winsize = (int(winsize[0]), int(winsize[1]))
        # Not an integer, no "x" in string
        except (ValueError, IndexError):
            self.winsize = (800, 600)
        self.resize(self.winsize[0], self.winsize[1])

        # Fullscreen
        if Gtk.get_minor_version() > 10:
            self.connect_data('window-state-event',
                              Window.on_window_state_change, self)
        else:
            self.connect_object('window-state-event',
                                Window.on_window_state_change, self)
        if start_fullscreen:
            self.toggle_fullscreen()

        # Auto resize
        self.connect("check-resize", self.auto_resize)
        # Focus changes with mouse
        for widget in [self.app["library"].treeview,
                       self.app["thumbnail"].iconview,
                       self.app["manipulate"].sliders["bri"],
                       self.app["manipulate"].sliders["con"],
                       self.app["manipulate"].sliders["sha"],
                       self.app["image"].image]:
            widget.connect("button-release-event", self.focus_on_mouse_click)

    def on_window_state_change(self, event, window=None):
        """Handle fullscreen/unfullscreen correctly.

        Args:
            event: Gtk event that called the function.
            window: Gtk.Window to operate on.
        """
        if window:
            window.is_fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                        & event.new_window_state)
        else:
            self.is_fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                      & event.new_window_state)

    def toggle_fullscreen(self):
        """Toggle fullscreen."""
        if self.is_fullscreen:
            self.unfullscreen()
        else:
            self.fullscreen()

    def auto_resize(self, window):
        """Automatically resize widgets when window is resized.

        Args:
            window: The window which emitted the resize event.
        """
        if self.get_size() != self.winsize:
            self.winsize = self.get_size()
            if self.app.paths:
                if self.app["thumbnail"].toggled:
                    self.app["thumbnail"].calculate_columns()
                if not self.app["image"].user_zoomed and \
                        not self.app["image"].is_anim:
                    self.app["image"].zoom_to(0)

    def focus_on_mouse_click(self, widget, event_button):
        """Update statusbar with the currently focused widget after mouse click.

        Args:
            widget: The widget that emitted the signal.
            event_button: Mouse button that was pressed.
        """
        self.app["statusbar"].update_info()

    def scroll(self, direction):
        """Scroll the correct object.

        Args:
            direction: Scroll direction to emit.
        """
        if direction not in scrolltypes:
            self.app["statusbar"].message(
                "Invalid scroll direction " + direction, "error")
        elif self.app["thumbnail"].toggled:
            self.app["thumbnail"].move_direction(direction)
        else:
            self.app["image"].scrolled_win.emit('scroll-child',
                                                scrolltypes[direction][0],
                                                scrolltypes[direction][1])
        return True  # Deactivates default bindings (here for Arrows)

    def zoom(self, zoom_in=True, step=1):
        """Zoom image or thumbnails.

        Args:
            zoom_in: If True, zoom in.
        """
        if self.app["thumbnail"].toggled:
            self.app["thumbnail"].zoom(zoom_in)
        else:
            self.app["image"].zoom_delta(zoom_in=zoom_in, step=step)
