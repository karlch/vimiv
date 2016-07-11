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
        self.timer_id_s = GLib.Timeout

    def toggle(self):
        """ Toggles the slideshow or updates the delay """
        if not self.vimiv.paths:
            self.vimiv.err_message("No valid paths, starting slideshow failed")
            return
        if self.vimiv.thumbnail.toggled:
            self.vimiv.err_message("Slideshow makes no sense in thumbnail mode")
            return
        # Delay changed via vimiv.keyhandler.num_str?
        if self.vimiv.keyhandler.num_str:
            self.set_delay(float(self.vimiv.keyhandler.num_str))
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.running = not self.running
            if self.running:
                self.timer_id_s = GLib.timeout_add(1000*self.delay,
                                                   self.vimiv.image.move_index,
                                                   True, False, 1)
            else:
                GLib.source_remove(self.timer_id_s)
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
            GLib.source_remove(self.timer_id_s)
            self.timer_id_s = GLib.timeout_add(1000*self.delay,
                                               self.vimiv.image.move_index,
                                               True, False, 1)
            self.vimiv.statusbar.update_info()
