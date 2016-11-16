#!/usr/bin/env python3
# encoding: utf-8
"""Main function for the vimiv image browser.

Parses the necessary stuff and starts the Gtk instance.
"""

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
    """Starting point for vimiv.

    Args:
        running_tests: If True running from testsuite. Do not run Gtk.main.
    """
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
    Vimiv(settings, paths, index).main()
    if not running_tests:
        Gtk.main()


class Vimiv(Gtk.Window):
    """"Actual vimiv class inheriting from Gtk.Window.

    Attributes:
        directory: Directory where configfiles and data is stored.
        paths: Paths for images.
        index: Position in paths.
        screensize: Available screensize.
        winsize: Size of the Gtk.Window.
        main_grid: Grid in which everything gets packed.
        keyhandler: Class to handle key-press events.
        commandline: Class for the commandline.
        tags: Class handling tags.
        mark: Class handling marks.
        fileextras: Class handling extra file actions.
        statusbar: Class for the statusbar.
        completions: Class handling completions.
        slideshow: Class handling slideshow.
        window: Class handling window events.
        image: Class for the image.
        library: Class for the library.
        thumbnail: Class for thumbnail mode.
        manipulate: Class handling manipulations.
        overlay: Gtk.Overlay with main_grid and floating commandline.
    """

    def __init__(self, settings, paths, index):
        """Create the necessary objects and settings.

        Args:
            settings: Settings from configfiles to use.
            paths: Paths received from the parser.
            index: Current position in paths.
        """
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
        self.fileextras = FileExtras(self)
        self.statusbar = Statusbar(self, settings)
        self.completions = VimivComplete(self)
        self.slideshow = Slideshow(self, settings)
        self.window = Window(self, settings)
        self.image = Image(self, settings)
        self.library = Library(self, settings)
        self.thumbnail = Thumbnail(self, settings)
        self.manipulate = Manipulate(self, settings)
        Commands(self, settings)

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

    def quit(self, force=False):
        """Quit the main loop, printi marked files and save history.

        Args:
            force: If True quit even if an image was edited.
        """
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

        Gtk.main_quit()

    def get_pos(self, get_filename=False):
        """Get the current position in the focused widget.

        get_filename: If True return filename instead of position.

        Return: Current position as Int or filename.
        """
        if not self.image.scrolled_win.is_focus():
            if self.library.treeview.is_focus():
                path = self.library.treeview.get_cursor()[0]
                filelist = self.library.files
            elif self.thumbnail.iconview.is_focus():
                path = self.thumbnail.iconview.get_cursor()[1]
                filelist = self.paths
            try:
                position = path.get_indices()[0]
                if get_filename:
                    return filelist[position]
                else:
                    return position
            except:
                if get_filename:
                    return ""
                else:
                    return 0
        else:
            if get_filename:
                return self.paths[self.index]
            else:
                return self.index

    def main(self):
        """Starting point for the vimiv class."""
        # Move to the directory of the image
        if self.paths:
            if isinstance(self.paths, list):
                os.chdir(os.path.dirname(self.paths[self.index]))
            else:
                os.chdir(self.paths)
                self.paths = []

        # Show everything and then hide whatever needs to be hidden
        self.show_all()
        self.manipulate.scrolled_win.hide()
        self.commandline.grid.hide()

        # Show the image if an imagelist exists
        if self.paths:
            self.image.move_index(True, False, 0)
            # Show library at the beginning?
            if not self.library.show_at_start:
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
            self.library.reload(os.getcwd())
            if self.library.expand:
                self.image.vimiv.image.scrolled_win.hide()
            self.statusbar.err_message("No valid paths, opening library viewer")
