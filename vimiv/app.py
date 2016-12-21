#!/usr/bin/env python
# encoding: utf-8
"""Main application class of vimiv."""

import os
import sys
from shutil import rmtree
from tempfile import mkdtemp
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib
from vimiv.configparser import parse_dirs, parse_config, set_defaults
from vimiv.image import Image
from vimiv.fileactions import FileExtras, populate
from vimiv.library import Library
from vimiv.thumbnail import Thumbnail
from vimiv.manipulate import Manipulate
from vimiv.statusbar import Statusbar
from vimiv.commandline import CommandLine
from vimiv.commands import Commands
from vimiv.completions import Completion
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
            widgets[widget-name] = Gtk.Widget
        directory: Directory in which configfiles and data are stored.
        commands: Dictionary of commands.
            commands[command-name] = [function, *args]
        aliases: Dicionary of aliases to commands.
            aliases[alias-name] = command-name
        functions: Dictionary of functions. Includes all commands and additional
            functions that cannot be called from the commandline.
        screensize: Available screensize.
    """

    def __init__(self, application_id="org.vimiv"):
        """Create the Gtk.Application and connect the activate signal.

        Args:
            application_id: The ID used to register vimiv. Default: org.vimiv.
        """
        # Init application and set default values
        Gtk.Application.__init__(self, application_id=application_id)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("activate", self.activate_vimiv)
        self.settings = {}
        self.paths = []
        self.index = 0
        self.widgets = {}
        self.directory = os.path.expanduser("~/.vimiv")
        self.commands = {}
        self.aliases = {}
        self.functions = {}
        # Set up all commandline options
        self.init_commandline_options()

    # Any different number of arguments will fail
    # pylint: disable=arguments-differ
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
        recursive = self.settings["GENERAL"]["recursive"]
        shuffle = self.settings["GENERAL"]["shuffle"]
        self.paths, self.index = populate(filenames, recursive, shuffle)

        # Activate vimiv after opening files
        self.activate_vimiv(self)

    # Any different number of arguments will fail
    # pylint: disable=arguments-differ
    def do_handle_local_options(self, options):
        """Handle commandline arguments.

        Args:
            options: The dictionary containing all options given to the
                commandline.
        Return:
            Exitcode or -1 to continue
        """
        def set_option(name, section, setting, value=0):
            """Set a setting in self.settings according to commandline option.

            Args:
                name: Name of the commandline option
                section: Name of section in self.settings to modify.
                setting: Name of setting in self.settings to modify.
                value: One of 0, 1 or 2.
                    0: Set setting to False.
                    1: Set setting to True.
                    2: Set setting to value given in the commandline.
            """
            if options.contains(name):
                valuedict = {0: False, 1: True}
                if value == 2:
                    valuedict[2] = options.lookup_value(name).unpack()
                self.settings[section][setting] = valuedict[value]

        # If the version option is given, print version and exit 0
        if options.contains("version"):
            information = Information()
            print(information.get_version())
            return 0
        # Temp basedir removes all current settings and sets them to default
        if options.contains("temp-basedir"):
            self.settings = set_defaults()
            self.directory = mkdtemp()
        # Create settings as soon as we know which config files to use
        elif options.contains("config"):
            local_config = options.lookup_value("config").unpack()
            self.settings = parse_config(local_config=local_config,
                                         system_config=None)
        else:
            self.settings = parse_config()

        # If we start from desktop, move to the wanted directory
        # Else if the input does not come from a tty, e.g. find "" | vimiv, set
        # paths and index according to the input from the pipe
        if options.contains("start-from-desktop"):
            os.chdir(self.settings["LIBRARY"]["desktop_start_dir"])
        elif not sys.stdin.isatty():
            tty_paths = []
            for line in sys.stdin:
                tty_paths.append(line.rstrip("\n"))
            self.paths, self.index = populate(tty_paths)

        set_option("bar", "GENERAL", "display_bar", 1)
        set_option("no-bar", "GENERAL", "display_bar", 0)
        set_option("library", "LIBRARY", "show_library", 1)
        set_option("no-library", "LIBRARY", "show_library", 0)
        set_option("fullscreen", "GENERAL", "start_fullscreen", 1)
        set_option("no-fullscreen", "GENERAL", "start_fullscreen", 0)
        set_option("shuffle", "GENERAL", "shuffle", 1)
        set_option("no-shuffle", "GENERAL", "shuffle", 0)
        set_option("recursive", "GENERAL", "recursive", 1)
        set_option("no-recursive", "GENERAL", "recursive", 0)
        set_option("slideshow", "GENERAL", "start_slideshow", 1)
        set_option("slideshow-delay", "GENERAL", "slideshow_delay", 2)
        set_option("geometry", "GENERAL", "geometry", 2)

        return -1  # To continue

    def activate_vimiv(self, app):
        """Starting point for the vimiv application.

        Args:
            app: The application itself.
        """
        parse_dirs(self.directory)
        self.init_widgets()
        self.create_window_structure()
        app.add_window(self["window"])
        # Show everything and then hide whatever needs to be hidden
        self["window"].show_all()
        self["manipulate"].scrolled_win.hide()
        self["commandline"].entry.hide()
        self["completions"].hide()
        # Statusbar depending on setting
        if self["statusbar"].hidden:
            self["statusbar"].bar.hide()
        self["statusbar"].set_separator_height()
        # Try to generate imagelist recursively from the current directory if
        # recursive is given and not paths exist
        if self.settings["GENERAL"]["recursive"] and not self.paths:
            shuffle = self.settings["GENERAL"]["shuffle"]
            self.paths, self.index = populate([os.getcwd()], True, shuffle)
        # Show the image if an imagelist exists
        if self.paths:
            self["image"].load_image()
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

    def init_widgets(self):
        """Create all the other widgets and add them to the class."""
        self["keyhandler"] = KeyHandler(self, self.settings)
        self["commandline"] = CommandLine(self, self.settings)
        self["tags"] = TagHandler(self)
        self["mark"] = Mark(self, self.settings)
        self["fileextras"] = FileExtras(self)
        self["statusbar"] = Statusbar(self, self.settings)
        self["completions"] = Completion(self)
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
        main_grid.attach(self["statusbar"].separator, 0, 2, 2, 1)

        overlay_grid = Gtk.Grid()
        overlay_grid.attach(self["statusbar"].bar, 0, 0, 1, 1)
        overlay_grid.attach(self["completions"].info, 0, 1, 1, 1)
        overlay_grid.attach(self["commandline"].entry, 0, 2, 1, 1)
        overlay_grid.set_valign(Gtk.Align.END)

        # Make it nice using CSS
        overlay_grid.set_name("CommandLine")
        style = Gtk.Window().get_style_context()
        color = style.get_background_color(Gtk.StateType.NORMAL)
        color_str = "#CommandLine { background-color: " + color.to_string() \
            + "; }"
        command_provider = Gtk.CssProvider()
        command_css = color_str.encode()
        command_provider.load_from_data(command_css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), command_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Overlay contains grid mainly and adds commandline as floating
        overlay = Gtk.Overlay()
        overlay.add(main_grid)
        overlay.add_overlay(overlay_grid)
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
        histfile = os.path.join(self.directory, "history")
        histfile = open(histfile, 'w')
        for cmd in self["commandline"].history:
            cmd += "\n"
            histfile.write(cmd)
        histfile.close()
        # Remove temporary directory
        if "/tmp/" in self.directory:
            rmtree(self.directory)
        # Call Gtk.Application.quit()
        self.quit()

    def get_pos(self, get_filename=False, force_widget=""):
        """Get the current position in the focused widget.

        get_filename: If True return filename instead of position.
        force_widget: String to force getting the position of a widget

        Return:
            Current position as number or filename.
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
            except:
                position = 0
                filelist = [""]
        else:
            filelist = self.paths
            position = self.index

        if get_filename:
            return filelist[position]
        else:
            return position

    def init_commandline_options(self):
        """Add all possible commandline options."""
        def add_option(name, short, help_str, flags=GLib.OptionFlags.NONE,
                       arg=GLib.OptionArg.NONE, value=None):
            """Add a single option.

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
        add_option("fullscreen", "f", "Start fullscreen")
        add_option("no-fullscreen", "F", "Do not start fullscreen")
        add_option("library", "l", "Display library")
        add_option("no-library", "L", "Hide library")
        add_option("recursive", "r", "Search directory recursively for images")
        add_option("no-recursive", "R",
                   "Do not search directory recursively for images")
        add_option("shuffle", "s", "Shuffle filelist")
        add_option("no-shuffle", "S", "Do not shuffle filelist")
        add_option("version", "v", "Print version information and exit")
        add_option("start-from-desktop", 0,
                   "Start using the desktop_start_dir as path")
        add_option("slideshow", 0, "Start slideshow at startup")
        add_option("slideshow-delay", 0, "Set slideshow delay",
                   arg=GLib.OptionArg.DOUBLE, value="delay")
        add_option("geometry", "g", "Set the starting geometry",
                   arg=GLib.OptionArg.STRING, value="GEOMETRY")
        add_option("temp-basedir", 0, "Use a temporary basedir")
        add_option("config", 0, "Use FILE as local configuration file",
                   arg=GLib.OptionArg.STRING, value="FILE")

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
