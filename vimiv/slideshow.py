#!/usr/bin/env python
# encoding: utf-8
""" Slideshow for vimiv """

from gi.repository import GLib


class Slideshow(object):
    """ Handles everything related to slideshow for vimiv """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        general = settings["GENERAL"]

        self.running = general["start_slideshow"]
        self.delay = general["slideshow_delay"]
        self.timer_id = GLib.Timeout
        self.start_index = 0

    def toggle(self):
        """ Toggles the slideshow or updates the delay """
        if not self.vimiv.paths:
            message = "No valid paths, starting slideshow failed"
            self.vimiv.statusbar.err_message(message)
            return
        if self.vimiv.thumbnail.toggled:
            message = "Slideshow makes no sense in thumbnail mode"
            self.vimiv.statusbar.err_message(message)
            return
        # Delay changed via vimiv.keyhandler.num_str?
        if self.vimiv.keyhandler.num_str:
            self.set_delay(float(self.vimiv.keyhandler.num_str))
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.running = not self.running
            if self.running:
                self.start_index = self.vimiv.index
                self.timer_id = GLib.timeout_add(1000 * self.delay,
                                                 self.vimiv.image.move_index,
                                                 True, False, 1)
            else:
                self.vimiv.statusbar.lock = False
                GLib.source_remove(self.timer_id)
        self.vimiv.statusbar.update_info()

    def set_delay(self, val, key=""):
        """ Sets slideshow delay to val or inc/dec depending on key """
        if key == "-":
            if self.delay >= 0.8:
                self.delay -= 0.2
        elif key == "+":
            self.delay += 0.2
        elif val:
            self.delay = float(val)
            self.vimiv.keyhandler.num_str = ""
        # If slideshow was running reload it
        if self.running:
            GLib.source_remove(self.timer_id)
            self.timer_id = GLib.timeout_add(1000 * self.delay,
                                               self.vimiv.image.move_index,
                                               True, False, 1)
            self.vimiv.statusbar.update_info()
