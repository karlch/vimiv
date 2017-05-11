# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Slideshow for vimiv."""

from gi.repository import GLib, GObject
from vimiv.helpers import get_float_from_str


class Slideshow(GObject.Object):
    """Handle everything related to slideshow for vimiv.

    Attributes:
        app: The main application class to interact with.
        at_start: If True start the slideshow after startup.
        default_delay: Slideshow delay set in the default settings.
        delay: Slideshow delay between images.
        timer_id: ID of the currently running GLib.Timeout.
        start_index: Index of the image when slideshow was started. Saved to
            display a message when slideshow is back at the beginning.
        running: If True the slideshow is running.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(Slideshow, self).__init__()
        self.app = app
        general = settings["GENERAL"]

        self.at_start = general["start_slideshow"]
        self.default_delay = general["slideshow_delay"]
        self.delay = general["slideshow_delay"]
        self.timer_id = GLib.Timeout
        self.start_index = 0
        self.running = False

    def toggle(self):
        """Toggle the slideshow or update the delay."""
        if not self.app.paths:
            message = "No valid paths, starting slideshow failed"
            self.app["statusbar"].message(message, "error")
            return
        if self.app["thumbnail"].toggled:
            message = "Slideshow makes no sense in thumbnail mode"
            self.app["statusbar"].message(message, "warning")
            return
        # Delay changed via vimiv["eventhandler"].num_str?
        if self.app["eventhandler"].num_str:
            self.set_delay(fixed_val=self.app["eventhandler"].num_str)
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.running = not self.running
            if self.running:
                self.start_index = self.app.index
                self.timer_id = GLib.timeout_add(1000 * self.delay,
                                                 self.app["image"].move_index,
                                                 True, False, 1)
            else:
                self.app["statusbar"].lock = False
                GLib.source_remove(self.timer_id)
        self.app["statusbar"].update_info()

    def set_delay(self, fixed_val=None, step=None):
        """Set slideshow delay.

        Args:
            fixed_val: Value to which the delay is set.
            step: Add step to the current delay.
        """
        val = fixed_val if fixed_val else self.default_delay
        # Parse step and fixed_val
        if step:
            step, errorcode = get_float_from_str(step)
            if errorcode:
                self.app["statusbar"].message(
                    "Argument for delay must be of type float", "error")
                return
            step *= self.app["eventhandler"].num_receive(1, True)
            self.delay += step
        elif val:
            val, errorcode = get_float_from_str(str(val))
            if errorcode:
                self.app["statusbar"].message(
                    "Argument for delay must be of type float", "error")
                return
            self.delay = val
            self.app["eventhandler"].num_clear()
        # Set a minimum
        if self.delay < 0.5:
            self.delay = 0.5
            self.app["statusbar"].message(
                "Delays shorter than 0.5 s are not allowed", "warning")
        # If slideshow was running reload it
        if self.running:
            GLib.source_remove(self.timer_id)
            self.timer_id = GLib.timeout_add(1000 * self.delay,
                                             self.app["image"].move_index,
                                             True, False, 1)
            self.app["statusbar"].update_info()
