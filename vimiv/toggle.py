#!/usr/bin/env python
# encoding: utf-8
""" Toggles fullscreen properly for vimiv """

from gi import require_version
require_version('Gdk', '3.0')
from gi.repository import Gdk

class FullscreenToggler(object):
    """ Toggles fullscreen properly for vimiv """

    def __init__(self, window, settings):
        self.window = window
        self.window_is_fullscreen = False
        self.window.connect_object('window-state-event',
                                   FullscreenToggler.on_window_state_change,
                                   self)

        # The configruations from vimivrc
        general = settings["GENERAL"]
        # library = settings["LIBRARY"]

        # General
        start_fullscreen = general["start_fullscreen"]
        if start_fullscreen:
            self.toggle()

    def on_window_state_change(self, event):
        self.window_is_fullscreen = bool(
            Gdk.WindowState.FULLSCREEN & event.new_window_state)

    def toggle(self):
        """ Toggles fullscreen """
        if self.window_is_fullscreen:
            self.window.unfullscreen()
        else:
            self.window.fullscreen()
        # Adjust the image if necessary
        if self.window.paths:
            if self.window.user_zoomed:
                self.window.update_image()
            else:
                self.window.zoom_to(0)


class VariableToggler(object):
    """ Toggles different variables for vimiv """

    def __init__(self, window, settings):
        self.window = window
        # The configruations from vimivrc
        general = settings["GENERAL"]
        self.overzoom = general["overzoom"]
        self.rescale_svg = general["rescale_svg"]
        # library = settings["LIBRARY"]

    def toggle_rescale_svg(self):
        self.rescale_svg = not self.rescale_svg

    def toggle_overzoom(self):
        self.overzoom = not self.overzoom
