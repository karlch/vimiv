#!/usr/bin/env python
# encoding: utf-8
"""Main application class of vimiv."""

import os
import sys
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib
from vimiv.configparser import parse_dirs, parse_config
from vimiv.image import Image
from vimiv.fileactions import FileExtras, populate
from vimiv.library import Library
from vimiv.thumbnail import Thumbnail
from vimiv.manipulate import Manipulate
from vimiv.statusbar import Statusbar
from vimiv.commandline import CommandLine
from vimiv.commands import Commands
from vimiv.completions import VimivComplete
from vimiv.slideshow import Slideshow
from vimiv.keyhandler import KeyHandler
from vimiv.tags import TagHandler
from vimiv.mark import Mark
from vimiv.information import Information
from vimiv.window import Window


class Vimiv(Gtk.Application):
    """Main vimiv application class inheriting from Gtk.Application.

    Attributes:
        settings: Settings from configfiles to use.
        paths: List of paths for images.
        index: Current position in paths.
        widgets: Dictionary of vimiv widgets.
            widgets[widgetname] = Gtk.Widget
        directory: Directory in which configfiles and data are stored.
        commands: Dictionary of commands.
            commands[commandname] = [function, *args]
        aliases: Dicionary of aliases to commands.
            aliases[aliasname] = commandname
        functions: Dictionary of functions. Includes all commands and additional
            functions that cannot be called from the commandline.
        screensize: Available screensize.
    """

    def __init__(self, application_id="org.vimiv"):
        """Create the Gtk.Application and connect the activate signal.

        Args:
            application_id: The ID used to register vimiv. Default: org.vimiv.
        """
        # Create directory structure and get settings
        parse_dirs()
        Gtk.Application.__init__(self, application_id=application_id)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("activate", self.activate_vimiv)
        self.settings = parse_config()
        self.paths = []
        self.index = 0
        self.widgets = {}
        self.directory = os.path.expanduser("~/.vimiv")
        self.commands = {}
        self.aliases = {}
        self.functions = {}
        # Sceen and window size TODO put somewhere else
        screen = Gdk.Screen()
        self.screensize = [screen.width(), screen.height()]
        # Set up all commandline options
        self.init_commandline_options()

    def do_open(self, files, n_files, hint):
        """Open files by populating self.paths and self.index.

        Args:
            files: List of Gio.Files.
            n_files: Number of files.
            hint: Special string for user, always empty in vimiv.
        """
        filenames = [fil.get_path() for fil in files]
        # Move to the directory of the first argument
        if os.path.isdir(filenames[0]):
            working_directory = filenames[0]
        else:
            working_directory = os.path.dirname(filenames[0])
        if os.path.exists(working_directory):
            os.chdir(working_directory)
        # Populate list of images
        self.paths, self.index = populate(filenames)

        # Activate vimiv after opening files
        self.activate_vimiv(self)

    def do_handle_local_options(self, options):
        """Handle commandline arguments.

        Args:
            command_line:
        """
        if options.contains("version"):
            information = Information()
            print(information.get_version())
            return 0  # To exit
        if options.contains("bar"):
            self.settings["GENERAL"]["display_bar"] = True
        elif options.contains("no-bar"):
            self.settings["GENERAL"]["display_bar"] = False
        if options.contains("library"):
            self.settings["LIBRARY"]["show_library"] = True
        elif options.contains("no-library"):
            self.settings["LIBRARY"]["show_library"] = False
        if options.contains("fullscreen"):
            self.settings["GENERAL"]["start_fullscreen"] = True
        elif options.contains("no-fullscreen"):
            self.settings["GENERAL"]["start_fullscreen"] = False
        if options.contains("shuffle"):
            self.settings["GENERAL"]["shuffle"] = True
        elif options.contains("no-shuffle"):
            self.settings["GENERAL"]["shuffle"] = False
        if options.contains("recursive"):
            self.settings["GENERAL"]["recursive"] = True
        elif options.contains("no-recursive"):
            self.settings["GENERAL"]["recursive"] = False
        if options.contains("slideshow"):
            self.settings["GENERAL"]["start_slideshow"] = True
        if options.contains("start-from-desktop"):
            os.chdir(self.settings["LIBRARY"]["desktop_start_dir"])
        elif not sys.stdin.isatty():
            tty_paths = []
            for line in sys.stdin:
                tty_paths.append(line.rstrip("\n"))
            self.paths, self.index = populate(tty_paths)
        if options.contains("slideshow-delay"):
            delay = options.lookup_value("slideshow-delay").unpack()
            self.settings["GENERAL"]["slideshow_delay"] = delay
        if options.contains("geometry"):
            geometry = options.lookup_value("geometry").unpack()
            self.settings["GENERAL"]["geometry"] = geometry
        return -1  # To continue

    def activate_vimiv(self, app):
        """Starting point for the vimiv application.

        Args:
            app: The application itself.
        """
        self.init_widgets()
        self.create_window_structure()
        app.add_window(self["window"])
        # Show everything and then hide whatever needs to be hidden
        self["window"].show_all()
        self["manipulate"].scrolled_win.hide()
        self["commandline"].grid.hide()
        # Statusbar depending on setting
        if self["statusbar"].hidden:
            self["statusbar"].bar.hide()

        # Show the image if an imagelist exists
        if self.paths:
            self["image"].move_index(True, False, 0)
            # Show library at the beginning?
            if not self["library"].show_at_start:
                self["library"].grid.hide()
            self["image"].scrolled_win.grab_focus()
            # Start in slideshow mode?
            if self["slideshow"].at_start:
                self["slideshow"].toggle()
        else:
            # Slideshow without paths makes no sense
            self["slideshow"].running = False
            self["library"].reload(os.getcwd())
            if self["library"].expand:
                self["image"].scrolled_win.hide()
            self["statusbar"].err_message(
                "No valid paths, opening library viewer")

    def set_settings(self, settings):
        """Set self.settings to settings."""
        self.settings = settings

    def set_paths(self, paths, index):
        """Set self.paths, self.index to paths, index."""
        self.paths = paths
        self.index = index

    def init_widgets(self):
        """Create all the other widgets and add them to the class."""
        self["keyhandler"] = KeyHandler(self, self.settings)
        self["commandline"] = CommandLine(self, self.settings)
        self["tags"] = TagHandler(self)
        self["mark"] = Mark(self, self.settings)
        self["fileextras"] = FileExtras(self)
        self["statusbar"] = Statusbar(self, self.settings)
        self["completions"] = VimivComplete(self)
        self["slideshow"] = Slideshow(self, self.settings)
        self["image"] = Image(self, self.settings)
        self["library"] = Library(self, self.settings)
        self["thumbnail"] = Thumbnail(self, self.settings)
        self["manipulate"] = Manipulate(self, self.settings)
        self["information"] = Information()
        self["window"] = Window(self, self.settings)
        Commands(self, self.settings)

    def create_window_structure(self):
        """Generate the structure of all the widgets and add it to the window.

        There is a large Gtk.Grid() to organize the widgets packed into a
        Gtk.Overlay(). The commandline is added as overlay.
        """
        main_grid = Gtk.Grid()
        main_grid.attach(self["library"].grid, 0, 0, 1, 1)
        main_grid.attach(self["image"].scrolled_win, 1, 0, 1, 1)
        main_grid.attach(self["manipulate"].scrolled_win, 0, 1, 2, 1)
        main_grid.attach(self["statusbar"].bar, 0, 2, 2, 1)

        # Overlay contains grid mainly and adds commandline as floating
        overlay = Gtk.Overlay()
        overlay.add(main_grid)
        overlay.add_overlay(self["commandline"].grid)
        self["window"].add(overlay)

    def quit_wrapper(self, force=False):
        """Quit the applications, print marked files and save history.

        Args:
            force: If True quit even if an image was edited.
        """
        for image in self["mark"].marked:
            print(image)
        # Check if image has been edited
        if self["image"].check_for_edit(force):
            return
        # Save the history
        histfile = os.path.expanduser("~/.vimiv/history")
        histfile = open(histfile, 'w')
        for cmd in self["commandline"].history:
            cmd += "\n"
            histfile.write(cmd)
        histfile.close()
        # Call Gtk.Application.quit()
        self.quit()

    def get_pos(self, get_filename=False, force_widget=""):
        """Get the current position in the focused widget.

        get_filename: If True return filename instead of position.
        force_widget: String to force getting the position of a widget

        Return:
            Current position as Int or filename.
        """
        # Find widget to work on
        if force_widget:
            focused_widget = force_widget
        elif self["image"].scrolled_win.is_focus():
            focused_widget = "im"
        elif self["library"].treeview.is_focus():
            focused_widget = "lib"
        elif self["thumbnail"].iconview.is_focus():
            focused_widget = "thu"

        # Get position and name
        if focused_widget != "im":
            if focused_widget == "lib":
                path = self["library"].treeview.get_cursor()[0]
                filelist = self["library"].files
            elif focused_widget == "thu":
                path = self["thumbnail"].iconview.get_cursor()[1]
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

    def init_commandline_options(self):
        """Add all possible commandline options."""
        def add_option(name, short, help_str, flags=GLib.OptionFlags.NONE,
                arg=GLib.OptionArg.NONE, value=None):
            """Adds a single option.

            Args:
                name: Long name of the option, called via --name.
                short: Short name of the option, called via -s.
                help_str: Displayed help text when calling --help.
                flags: GLib options.
                arg: Type of the value to give after option.
                value: Name of the value to give after the option.
            """
            if short:
                short = ord(short)
            self.add_main_option(name, short, flags, arg, help_str, value)
        add_option("bar", "b", "Display statusbar")
        add_option("no-bar", "B", "Hide statusbar")
        add_option("library", "l", "Display library")
        add_option("no-library", "L", "Hide library")
        add_option("fullscreen", "f", "Start fullscreen")
        add_option("no-fullscreen", "F", "Do not start fullscreen")
        add_option("shuffle", "s", "Shuffle filelist")
        add_option("no-shuffle", "S", "Do not shuffle filelist")
        add_option("recursive", "r", "Search directory recursively for images")
        add_option("no-recursive", "R",
                   "Do not search directory recursively for images")
        add_option("version", "v", "Print version information and exit")
        add_option("slideshow", 0, "Start slideshow at startup")
        add_option("start-from-desktop", 0,
                   "Start using the desktop_start_dir as path")
        add_option("slideshow-delay", 0, "Set slideshow delay",
                   arg=GLib.OptionArg.DOUBLE, value="delay")
        add_option("geometry", "g", "Set the starting geometry",
                   arg=GLib.OptionArg.STRING, value="GEOMETRY")

    def __getitem__(self, name):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to access.
        Return:
            The widget if it exists. None else.
        """
        if name in self.widgets:
            return self.widgets[name]
        else:
            return None

    def __setitem__(self, name, widget):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to add.
            item: The actual widget to which name will refer.
        """
        self.widgets[name] = widget

    def __contains__(self, name):
        """Return True if a widget called name exists."""
        return name in self.widgets
