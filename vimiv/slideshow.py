# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Slideshow for vimiv."""

from gi.repository import GLib, GObject
from vimiv.helpers import get_float_from_str


class Slideshow(GObject.Object):
    """Handle everything related to slideshow for vimiv.

    Attributes:
        running: If True the slideshow is running.

        _app: The main application class to interact with.
        _default_delay: Slideshow delay set in the default settings.
        _delay: Slideshow delay between images.
        _start_index: Index of the image when slideshow was started. Saved to
            display a message when slideshow is back at the beginning.
        _timer_id: ID of the currently running GLib.Timeout.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(Slideshow, self).__init__()
        self._app = app
        general = settings["GENERAL"]

        self._default_delay = general["slideshow_delay"]
        self._delay = general["slideshow_delay"]
        self._start_index = 0
        self.running = False
        self._timer_id = GLib.Timeout

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
        if self._app["eventhandler"].num_str:
            self.set_delay(fixed_val=self._app["eventhandler"].num_str)
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.running = not self.running
            if self.running:
                self._start_index = self._app.get_index()
                self._timer_id = GLib.timeout_add(1000 * self._delay,
                                                  self._next)
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

    def set_delay(self, fixed_val=None, step=None):
        """Set slideshow delay.

        Args:
            fixed_val: Value to which the delay is set.
            step: Add step to the current delay.
        """
        val = fixed_val if fixed_val else self._default_delay
        # Parse step and fixed_val
        if step:
            step, errorcode = get_float_from_str(step)
            if errorcode:
                self._app["statusbar"].message(
                    "Argument for delay must be of type float", "error")
                return
            step *= self._app["eventhandler"].num_receive(1, True)
            self._delay += step
        elif val:
            val, errorcode = get_float_from_str(str(val))
            if errorcode:
                self._app["statusbar"].message(
                    "Argument for delay must be of type float", "error")
                return
            self._delay = val
            self._app["eventhandler"].num_clear()
        # Set a minimum
        if self._delay < 0.5:
            self._delay = 0.5
            self._app["statusbar"].message(
                "Delays shorter than 0.5 s are not allowed", "warning")
        # If slideshow was running reload it
        if self.running:
            GLib.source_remove(self._timer_id)
            self._timer_id = GLib.timeout_add(1000 * self._delay, self._next)
            self._app["statusbar"].update_info()

    def get_formatted_delay(self):
        """Return the delay formatted neatly for the statusbar."""
        return "[slideshow - {0:.1f}s]".format(self._delay)

    # These are for the test suite
    def get_delay(self):
        return self._delay

    def get_default_delay(self):
        return self._default_delay
