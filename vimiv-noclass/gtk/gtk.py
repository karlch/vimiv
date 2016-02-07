#!/usr/bin/env python
# encoding: utf-8
""" The actual Vimiv GTK Class """

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv.gtk.image import move_index, auto_resize
from vimiv.gtk.widgets import main_box_generate


class Vimiv(Gtk.Window):
    """ Vimiv class, subclass of a Gtk.Window """

    def __init__(self, settings, paths, index):
        # Screen
        self.screen = Gdk.Screen()
        self.screensize = [self.screen.width(), self.screen.height()]
        # General vimiv variables
        self.settings = settings
        self.paths = paths
        self.index = index
        self.user_zoomed = False
        self.thumbnail_toggled = False
        self.animation_toggled = False
        # Box for everything
        self.box = Gtk.Box()

        # Initialize the Gtk Window
        Gtk.Window.__init__(self)

    def main(self):
        # Move to the directory of the image
        if self.paths:
            os.chdir(os.path.dirname(self.paths[self.index]))

        # Gtk window with general settings
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('destroy', Gtk.main_quit)
        self.connect("check-resize", auto_resize, self)
        self.set_icon_name("image-x-generic")

        self.box = main_box_generate(self)

        self.show_all()

        # # Statusbar on the bottom
        #
        # # Box with the statusbar and the command line
        #
        # # Size for resizing image
        # self.statusbar_size = self.labelbox.get_allocated_height()
        #
        # # Set the window size
        # self.resize(self.winsize[0], self.winsize[1])
        # if self.fullscreen_toggled:
        #     self.fullscreen()
        #
        # self.show_all()
        # # Hide the manipulate bar and the command line
        # self.hboxman.hide()
        # self.cmd_line_box.hide()
        #
        # # Show images, if a path was given
        # if self.paths:
        move_index(self)
        #     # Show library at the beginning?
        #     if self.library_toggled:
        #         self.boxlib.show()
        #     else:
        #         self.boxlib.hide()
        #     self.scrolled_win.grab_focus()
        #     if self.fullscreen_toggled:
        #         self.fullscreen()
        #     # Start in slideshow mode?
        #     if self.slideshow:
        #         self.slideshow = False
        #         self.toggle_slideshow()
        #     self.toggle_statusbar()
        # else:
        #     self.slideshow = False  # Slideshow without paths makes no sense
        #     self.toggle_statusbar()
        #     self.library_focus(True)
        #     if self.expand_lib:
        #         self.grid.set_size_request(self.winsize[0], 10)
        #     self.err_message("No valid paths, opening library viewer")

        # Finally show the main window
        Gtk.main()
