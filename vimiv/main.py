#!/usr/bin/env python3
# encoding: utf-8
""" Main function for the vimiv image browser
Parses the necessary stuff and starts the Gtk instance """

import os
import signal
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv.parser import get_args, parse_dirs, parse_config, parse_args
from vimiv.fileactions import populate, FileExtras
from vimiv.image import Image
from vimiv.library import Library
from vimiv.thumbnail import Thumbnail
from vimiv.manipulate import Manipulate
from vimiv.statusbar import Statusbar
from vimiv.commandline import CommandLine
from vimiv.commands import Commands
from vimiv.completions import VimivComplete
from vimiv.slideshow import Slideshow
from vimiv.events import KeyHandler, Window
from vimiv.tags import TagHandler
from vimiv.mark import Mark


def main(running_tests=False):
    """ Starting point for vimiv """
    parser = get_args()
    parse_dirs()
    settings = parse_config()
    settings = parse_args(parser, settings)

    args = settings["GENERAL"]["paths"]

    # Recursive and shuffling requiered immediately by populate
    recursive = settings["GENERAL"]["recursive"]
    shuffle_paths = settings["GENERAL"]["shuffle"]

    paths, index = populate(args, recursive, shuffle_paths)
    # Start the actual window
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    if not running_tests:
        Vimiv(settings, paths, index).main()
        Gtk.main()
    else:
        vimiv = Vimiv(settings, paths, index)
        vimiv.main(True)
        vimiv.quit(running_tests=True)


class Vimiv(Gtk.Window):
    """" Actual vimiv class as a Gtk Window """

    def __init__(self, settings, paths, index):

        Gtk.Window.__init__(self)
        self.connect('destroy', Gtk.main_quit)

        # Own stuff
        general = settings["GENERAL"]
        self.directory = os.path.expanduser("~/.vimiv")
        self.paths = paths
        self.index = index
        self.set_icon_name("vimiv")

        # Sceen and window size
        screen = Gdk.Screen()
        self.screensize = [screen.width(), screen.height()]
        try:
            winsize = general["geometry"].split("x")
            self.winsize = (int(winsize[0]), int(winsize[1]))
            self.resize(self.winsize[0], self.winsize[1])
        except:
            self.winsize = (800, 600)
            self.resize(self.winsize[0], self.winsize[1])

        # Generate Window structure
        # Grid in which everything gets packed
        self.main_grid = Gtk.Grid()

        # Other classes
        self.keyhandler = KeyHandler(self, settings)
        self.commandline = CommandLine(self, settings)
        self.tags = TagHandler(self)
        self.mark = Mark(self, settings)
        self.fileextras = FileExtras(self, settings)
        self.statusbar = Statusbar(self, settings)
        self.completions = VimivComplete(self)
        self.slideshow = Slideshow(self, settings)
        self.window = Window(self, settings)
        self.image = Image(self, settings)
        self.library = Library(self, settings)
        self.thumbnail = Thumbnail(self, settings)
        self.manipulate = Manipulate(self, settings)
        Commands(self)

        # Pack library, statusbar and manipulate
        self.main_grid.attach(self.library.grid, 0, 0, 1, 1)
        self.main_grid.attach(self.image.scrolled_win, 1, 0, 1, 1)
        self.main_grid.attach(self.manipulate.scrolled_win, 0, 1, 2, 1)
        self.main_grid.attach(self.statusbar.bar, 0, 2, 2, 1)

        # Overlay contains grid mainly and adds commandline as floating
        self.overlay = Gtk.Overlay()
        self.overlay.add(self.main_grid)
        self.overlay.add_overlay(self.commandline.grid)
        self.add(self.overlay)

    def quit(self, force=False, running_tests=False):
        """ Quit the main loop, printing marked files and saving history """
        for image in self.mark.marked:
            print(image)
        # Check if image has been edited
        if self.image.check_for_edit(force):
            return
        # Save the history
        histfile = os.path.expanduser("~/.vimiv/history")
        histfile = open(histfile, 'w')
        for cmd in self.commandline.history:
            cmd += "\n"
            histfile.write(cmd)
        histfile.close()

        if not running_tests:
            Gtk.main_quit()

    def main(self, running_tests=False):
        # Move to the directory of the image
        if self.paths:
            if isinstance(self.paths, list):
                os.chdir(os.path.dirname(self.paths[self.index]))
            else:
                os.chdir(self.paths)
                self.paths = []

        # Show everything and then hide whatever needs to be hidden
        if not running_tests:
            self.show_all()
        self.manipulate.scrolled_win.hide()
        self.commandline.grid.hide()

        # Show the image if an imagelist exists
        if self.paths:
            self.image.move_index(True, False, 0)
            # Show library at the beginning?
            if self.library.toggled:
                self.library.grid.show()
            else:
                self.library.grid.hide()
            self.image.scrolled_win.grab_focus()
            # Start in slideshow mode?
            if self.slideshow.at_start:
                self.slideshow.toggle()
            self.statusbar.toggle()
        # Just open the library if no paths were given
        else:
            # Slideshow without paths makes no sense
            self.slideshow.running = False
            self.statusbar.toggle()
            self.library.focus(True)
            if self.library.expand:
                self.library.scrollable_treeview.set_size_request(
                    self.winsize[0], 10)
            self.statusbar.err_message("No valid paths, opening library viewer")
