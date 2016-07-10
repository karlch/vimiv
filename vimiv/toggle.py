#!/usr/bin/env python
# encoding: utf-8
""" Toggles fullscreen properly for vimiv """

from gi.repository import Gdk

class FullscreenToggler(object):
    """ Toggles fullscreen properly for vimiv """

    def __init__(self, window, start_fullscreen):
        self.window = window
        self.window_is_fullscreen = False
        self.window.connect_object('window-state-event',
                                   FullscreenToggler.on_window_state_change,
                                   self)
        if start_fullscreen:
            self.toggle()

    def on_window_state_change(self, event):
        self.window_is_fullscreen = bool(
            Gdk.WindowState.FULLSCREEN & event.new_window_state)

    def toggle(self):
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
