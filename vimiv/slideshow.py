#!/usr/bin/env python
# encoding: utf-8
"""Slideshow for vimiv."""

from gi.repository import GLib


class Slideshow(object):
    """Handle everything related to slideshow for vimiv.

    Attributes:
        app: The main application class to interact with.
        at_start: If True start the slideshow after startup.
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
        self.app = app
        general = settings["GENERAL"]

        self.at_start = general["start_slideshow"]
        self.delay = general["slideshow_delay"]
        self.timer_id = GLib.Timeout
        self.start_index = 0
        self.running = False

    def toggle(self):
        """Toggle the slideshow or update the delay."""
        if not self.app.paths:
            message = "No valid paths, starting slideshow failed"
            self.app["statusbar"].err_message(message)
            return
        if self.app["thumbnail"].toggled:
            message = "Slideshow makes no sense in thumbnail mode"
            self.app["statusbar"].err_message(message)
            return
        # Delay changed via vimiv["keyhandler"].num_str?
        if self.app["keyhandler"].num_str:
            self.set_delay(float(self.app["keyhandler"].num_str))
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

    def set_delay(self, val=None, key=""):
        """Set slideshow delay.

        Args:
            val: Value to which the delay is set.
            key: One of "+" or "-" indicating if the delay should be increased
                or decreased.
        """
        val = val if val else self.app.settings["GENERAL"]["slideshow_delay"]
        if key == "-":
            if self.delay >= 0.8:
                self.delay -= 0.2
        elif key == "+":
            self.delay += 0.2
        elif val:
            self.delay = float(val)
            self.app["keyhandler"].num_clear()
        # If slideshow was running reload it
        if self.running:
            GLib.source_remove(self.timer_id)
            self.timer_id = GLib.timeout_add(1000 * self.delay,
                                             self.app["image"].move_index,
                                             True, False, 1)
            self.app["statusbar"].update_info()
