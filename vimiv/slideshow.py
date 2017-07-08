# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Slideshow for vimiv."""

from gi.repository import GLib, GObject
from vimiv.settings import settings


class Slideshow(GObject.Object):
    """Handle everything related to slideshow for vimiv.

    Attributes:
        running: If True the slideshow is running.

        _app: The main application class to interact with.
        _start_index: Index of the image when slideshow was started. Saved to
            display a message when slideshow is back at the beginning.
        _timer_id: ID of the currently running GLib.Timeout.
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        super(Slideshow, self).__init__()
        self._app = app

        self._start_index = 0
        self.running = False
        self._timer_id = GLib.Timeout
        settings.connect("changed", self._on_settings_changed)

    def toggle(self):
        """Toggle the slideshow or update the delay."""
        if not self._app.get_paths():
            message = "No valid paths, starting slideshow failed"
            self._app["statusbar"].message(message, "error")
            return
        if self._app["thumbnail"].toggled:
            message = "Slideshow makes no sense in thumbnail mode"
            self._app["statusbar"].message(message, "warning")
            return
        # Delay changed via vimiv["eventhandler"].num_str?
        number = self._app["eventhandler"].get_num_str()
        if number:
            settings.override("slideshow_delay", number)
            self._app["eventhandler"].num_clear()
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.running = not self.running
            if self.running:
                delay = 1000 * settings["slideshow_delay"].get_value()
                self._start_index = self._app.get_index()
                self._timer_id = GLib.timeout_add(delay, self._next)
            else:
                self._app["statusbar"].lock = False
                GLib.source_remove(self._timer_id)
        self._app["statusbar"].update_info()

    def _next(self):
        """Command to run in the GLib.timeout moving to the next image."""
        self._app["image"].move_index()
        # Info if slideshow returns to beginning
        if self._app.get_index() == self._start_index:
            message = "Back at beginning of slideshow"
            self._app["statusbar"].lock = True
            self._app["statusbar"].message(message, "info")
        else:
            self._app["statusbar"].lock = False
        return True  # So we continue running

    def get_formatted_delay(self):
        """Return the delay formatted neatly for the statusbar."""
        delay = settings["slideshow_delay"].get_value()
        return "[slideshow - {0:.1f}s]".format(delay)

    def _on_settings_changed(self, new_settings, setting):
        if setting == "slideshow_delay":
            delay = settings["slideshow_delay"].get_value()
            # Set a minimum
            if delay < 0.5:
                settings.override("slideshow_delay", "0.5")
                self._app["statusbar"].message(
                    "Delays shorter than 0.5 s are not allowed", "warning")
                return
            # If slideshow was running reload it
            if self.running:
                GLib.source_remove(self._timer_id)
                self._timer_id = GLib.timeout_add(1000 * delay, self._next)
                self._app["statusbar"].update_info()
