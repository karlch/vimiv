# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Window class for vimiv."""

from gi.repository import Gdk, Gtk
from vimiv.settings import settings


class Window(Gtk.ApplicationWindow):
    """"Vimiv Window containing the general structure.

    Additionally handles events like fullscreen and resize.

    Attributes:
        winsize: The windowsize as tuple.

        _app: The main vimiv application to interact with.
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        super(Window, self).__init__()

        self._app = app

        self.connect("destroy", self._app.quit_wrapper)
        self.connect("button_press_event", self._app["eventhandler"].on_click,
                     "IMAGE")
        self.connect("touch-event", self._app["eventhandler"].on_touch)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)

        # Set initial window size
        self.winsize = settings["geometry"].get_value()
        self.resize(self.winsize[0], self.winsize[1])

        if settings["start_fullscreen"].get_value():
            self.toggle_fullscreen()

        # Auto resize
        self.connect("check-resize", self._auto_resize)
        # Focus changes with mouse
        for widget in [self._app["library"],
                       self._app["thumbnail"],
                       self._app["manipulate"].sliders["bri"],
                       self._app["manipulate"].sliders["con"],
                       self._app["manipulate"].sliders["sat"],
                       self._app["image"]]:
            widget.connect("button-release-event", self._on_click)

    def toggle_fullscreen(self):
        """Toggle fullscreen."""
        if self.get_window().get_state() & Gdk.WindowState.FULLSCREEN:
            self.unfullscreen()
        else:
            self.fullscreen()

    def zoom(self, zoom_in=True, step=1):
        """Zoom image or thumbnails.

        Args:
            zoom_in: If True, zoom in.
        """
        if self._app["thumbnail"].toggled:
            self._app["thumbnail"].zoom(zoom_in)
        else:
            self._app["image"].zoom_delta(zoom_in=zoom_in, step=step)

    def _auto_resize(self, window):
        """Automatically resize widgets when window is resized.

        Args:
            window: The window which emitted the resize event.
        """
        if self.get_size() != self.winsize:
            self.winsize = self.get_size()
            self._app.emit("widget-layout-changed", self)

    def _on_click(self, widget, event_button):
        """Update statusbar with the currently focused widget after mouse click.

        Args:
            widget: The widget that emitted the signal.
            event_button: Mouse button that was pressed.
        """
        self._app["statusbar"].update_info()
