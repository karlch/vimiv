# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Main application class of vimiv."""

import os
import sys
import tempfile
from time import time

from gi.repository import Gdk, Gio, GLib, Gtk, GObject
from vimiv.commandline import CommandLine
from vimiv.commands import Commands
from vimiv.completions import Completion
from vimiv.configparser import parse_config, set_defaults
from vimiv.eventhandler import KeyHandler
from vimiv.fileactions import FileExtras, populate
from vimiv.information import Information
from vimiv.library import Library
from vimiv.log import Log
from vimiv.main_window import MainWindow
from vimiv.manipulate import Manipulate
from vimiv.mark import Mark
from vimiv.slideshow import Slideshow
from vimiv.statusbar import Statusbar
from vimiv.tags import TagHandler
from vimiv.window import Window


class Vimiv(Gtk.Application):
    """Main vimiv application class inheriting from Gtk.Application.

    Attributes:
        settings: Settings from configfiles to use.
        paths: List of paths for images.
        index: Current position in paths.
        widgets: Dictionary of vimiv widgets.
            widgets[widget-name] = Gtk.Widget
        debug: If True, write all messages and commands to log.
        tmpdir: tmpfile.TemporaryDirectory used when running with --temp-basedir
        commands: Dictionary of commands.
            commands[command-name] = [function, *args]
        aliases: Dicionary of aliases to commands.
            aliases[alias-name] = command-name
        functions: Dictionary of functions. Includes all commands and additional
            functions that cannot be called from the commandline.
        screensize: Available screensize.

    Signals:
        widgets-changed: Emitted when the layout of the widgets changed in some
            way. This allows other widgets to trigger an update when this
            happens, e.g. rezoom an image when the library was toggled.
        paths-changed: Emmited when the paths have or may have changed. This
            allows other widgets to reload their filelist and update any
            information accordingly.
    """

    def __init__(self, running_tests=False):
        """Create the Gtk.Application and connect the activate signal.

        Args:
            running_tests: If True, running from test suite. Do not show pop-up
                windows and do not parse user configuration files.
        """
        # Init application and set default values
        app_id = "org.vimiv" + str(time()).replace(".", "")
        super(Vimiv, self).__init__(application_id=app_id)
        self.set_flags(Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("activate", self.activate_vimiv)
        self.settings = {}
        self.paths = []
        self.index = 0
        self.widgets = {}
        self.debug = False
        self.tmpdir = None
        self.commands = {}
        self.aliases = {}
        self.functions = {}
        self.running_tests = running_tests
        # Set up signals
        try:
            GObject.signal_new("widgets-changed", self, GObject.SIGNAL_RUN_LAST,
                               GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,))
            GObject.signal_new("paths-changed", self, GObject.SIGNAL_RUN_LAST,
                               GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,))
        # TODO Happens in tests, needs to be investigated
        except RuntimeError:
            pass
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
        recursive = self.settings["GENERAL"]["recursive"]
        shuffle = self.settings["GENERAL"]["shuffle"]
        self.paths, self.index = populate(filenames, recursive, shuffle)

        # Activate vimiv after opening files
        self.activate_vimiv(self)

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

        # Show Gtk warnings if the debug option is given
        if options.contains("debug"):
            self.debug = True
        # If the version option is given, print version and exit 0
        if options.contains("version"):
            information = Information()
            print(information.get_version())
            return 0
        # Temp basedir removes all current settings and sets them to default
        if options.contains("temp-basedir"):
            self.tmpdir = tempfile.TemporaryDirectory(prefix="vimiv-")
            self.settings = set_defaults()
            tmp = self.tmpdir.name
            # Export environment variables for thumbnails, tags, history and
            # logs
            os.environ["XDG_CACHE_HOME"] = os.path.join(tmp, "cache")
            os.environ["XDG_CONFIG_HOME"] = os.path.join(tmp, "config")
            os.environ["XDG_DATA_HOME"] = os.path.join(tmp, "data")
        # Create settings as soon as we know which config files to use
        elif options.contains("config"):
            configfile = options.lookup_value("config").unpack()
            self.settings = parse_config(commandline_config=configfile,
                                         running_tests=self.running_tests)
        else:
            self.settings = parse_config(running_tests=self.running_tests)

        # If we start from desktop, move to the wanted directory
        # Else if the input does not come from a tty, e.g. find "" | vimiv, set
        # paths and index according to the input from the pipe
        if options.contains("start-from-desktop"):
            os.chdir(self.settings["LIBRARY"]["desktop_start_dir"])
        elif not sys.stdin.isatty():
            try:
                tty_paths = []
                for line in sys.stdin:
                    tty_paths.append(line.rstrip("\n"))
                self.paths, self.index = populate(tty_paths)
            except TypeError:
                pass  # DebugConsoleStdIn is not iterable

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
        self.init_widgets()
        self.create_window_structure()
        app.add_window(self["window"])
        # Show everything and then hide whatever needs to be hidden
        self["window"].show_all()
        self["manipulate"].hide()
        self["commandline"].hide()
        self["completions"].hide()
        # Statusbar depending on setting
        if self["statusbar"].hidden:
            self["statusbar"].hide()
        self["statusbar"].set_separator_height()
        # Try to generate imagelist recursively from the current directory if
        # recursive is given and not paths exist
        if self.settings["GENERAL"]["recursive"] and not self.paths:
            shuffle = self.settings["GENERAL"]["shuffle"]
            self.paths, self.index = populate([os.getcwd()], True, shuffle)
        # Show the image if an imagelist exists
        if self.paths:
            self["image"].load()
            # Show library at the beginning?
            if not self["library"].show_at_start:
                self["library"].grid.hide()
            self["main_window"].grab_focus()
            # Start in slideshow mode?
            if self["slideshow"].at_start:
                self["slideshow"].toggle()
        else:
            # Slideshow without paths makes no sense
            self["slideshow"].running = False
            self["library"].focus()
            if self["library"].expand:
                self["main_window"].hide()

    def init_widgets(self):
        """Create all the other widgets and add them to the class."""
        self["eventhandler"] = KeyHandler(self, self.settings)
        self["commandline"] = CommandLine(self, self.settings)
        self["tags"] = TagHandler(self)
        self["mark"] = Mark(self, self.settings)
        self["fileextras"] = FileExtras(self)
        self["statusbar"] = Statusbar(self, self.settings)
        self["completions"] = Completion(self)
        self["slideshow"] = Slideshow(self, self.settings)
        self["main_window"] = MainWindow(self, self.settings)
        self["image"] = self["main_window"].image
        self["thumbnail"] = self["main_window"].thumbnail
        self["library"] = Library(self, self.settings)
        self["manipulate"] = Manipulate(self, self.settings)
        self["information"] = Information()
        self["window"] = Window(self, self.settings)
        self["commands"] = Commands(self, self.settings).commands
        # Generate completions as soon as commands exist
        self["completions"].generate_commandlist()
        self["log"] = Log(self)

    def create_window_structure(self):
        """Generate the structure of all the widgets and add it to the window.

        There is a large Gtk.Grid() to organize the widgets packed into a
        Gtk.Overlay(). The commandline is added as overlay.
        """
        main_grid = Gtk.Grid()
        main_grid.attach(self["library"].grid, 0, 0, 1, 1)
        main_grid.attach(self["main_window"], 1, 0, 1, 1)
        main_grid.attach(self["manipulate"], 0, 1, 2, 1)
        main_grid.attach(self["statusbar"].separator, 0, 2, 2, 1)

        overlay_grid = Gtk.Grid()
        overlay_grid.attach(self["statusbar"], 0, 0, 1, 1)
        overlay_grid.attach(self["completions"].info, 0, 1, 1, 1)
        overlay_grid.attach(self["commandline"], 0, 2, 1, 1)
        overlay_grid.set_valign(Gtk.Align.END)

        # Make it nice using CSS
        overlay_grid.set_name("OverLay")
        style = Gtk.Window().get_style_context()
        bg = style.get_background_color(Gtk.StateType.NORMAL)
        color_str = "#OverLay { background: " + bg.to_string() + "; }"
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
        # Check for running external processes
        if self["commandline"].running_processes:
            if force:
                for p in self["commandline"].running_processes:
                    p.kill()
            else:
                processes = [p.args
                             for p in self["commandline"].running_processes]
                message = "Running external processes: %s. Add ! to force." \
                          % (", ".join(processes))
                self["statusbar"].message(message, "warning")
                return
        # Check if image has been edited
        if self["manipulate"].check_for_edit(force):
            return
        for image in self["mark"].marked:
            print(image)
        # Run remaining rotate and flip threads
        self["manipulate"].thread_for_simple_manipulations()
        # Save the history
        histfile = os.path.join(GLib.get_user_data_dir(), "vimiv", "history")
        histfile = open(histfile, "w")
        for cmd in self["commandline"].history:
            cmd += "\n"
            histfile.write(cmd)
        histfile.close()
        # Write to log
        self["log"].write_message("Exited", "time")
        # Cleanup tmpdir
        if self.tmpdir:
            self.tmpdir.cleanup()
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
        elif self["main_window"].is_focus() or \
                self["manipulate"].is_visible():
            focused_widget = "im"
        elif self["library"].is_focus():
            focused_widget = "lib"
        elif self["thumbnail"].is_focus():
            focused_widget = "thu"

        # Get position and name
        if focused_widget != "im":
            if focused_widget == "lib":
                path = self["library"].get_cursor()[0]
                filelist = self["library"].files
            elif focused_widget == "thu":
                path = self["thumbnail"].get_cursor()[1]
                filelist = self.paths
            if path:
                position = path.get_indices()[0]
            else:
                position = 0
                filelist = [""]
        else:
            filelist = self.paths
            position = self.index

        if get_filename:
            return filelist[position] if filelist else ""
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
        add_option("debug", 0, "Run in debug mode")

    def __getitem__(self, name):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to access.
        Return:
            The widget if it exists. None else.
        """
        if name in self.widgets:
            return self.widgets[name]
        return None

    def __setitem__(self, name, widget):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to add.
            item: The actual widget to which name will refer.
        """
        self.widgets[name] = widget
