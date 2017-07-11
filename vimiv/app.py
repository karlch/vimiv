# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Main application class of vimiv."""

import os
import sys
import tempfile
from time import time

from gi.repository import Gdk, Gio, GLib, GObject, Gtk
from vimiv.commandline import CommandLine
from vimiv.completions import Completion
from vimiv.config_parser import parse_config
from vimiv.eventhandler import EventHandler
from vimiv.fileactions import FileExtras, populate
from vimiv.information import Information
from vimiv.library import Library
from vimiv.log import Log
from vimiv.main_window import MainWindow
from vimiv.manipulate import Manipulate
from vimiv.mark import Mark
from vimiv.settings import settings
from vimiv.slideshow import Slideshow
from vimiv.statusbar import Statusbar
from vimiv.tags import TagHandler
from vimiv.transform import Transform
from vimiv.window import Window


class Vimiv(Gtk.Application):
    """Main vimiv application class inheriting from Gtk.Application.

    Attributes:
        debug: If True, write all messages and commands to log.

        _tmpdir: tmpfile.TemporaryDirectory used when running with
            --temp-basedir
        _widgets: Dictionary of vimiv widgets.
            widgets[widget-name] = Gtk.Widget
        _paths: List of paths for images.
        _index: Current position in paths.

    Signals:
        widget-layout-changed: Emitted when the layout of the widgets changed in
            some way. This allows other widgets to trigger an update when this
            happens, e.g. rezoom an image when the library was toggled.
        paths-changed: Emitted when the paths have or may have changed. This
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
        self._paths = []
        self._index = 0
        self._widgets = {}
        self.debug = False
        self._tmpdir = None
        self.running_tests = running_tests
        # Set up all commandline options
        self._init_commandline_options()

    def do_open(self, files, n_files, hint):
        """Open files by populating self._paths and self._index.

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
        recursive = settings["recursive"].get_value()
        shuffle = settings["shuffle"].get_value()
        self.populate(filenames, recursive=recursive, shuffle_paths=shuffle)

        # Activate vimiv after opening files
        self.activate_vimiv(self)

    def do_handle_local_options(self, options):
        """Handle commandline arguments.

        Args:
            options: The dictionary containing all options given to the
                commandline.
        Return:
            Exit-code or -1 to continue
        """
        def set_option(name, setting, value=0):
            """Set a setting in settings according to commandline option.

            Args:
                name: Name of the commandline option
                setting: Name of setting in settings to modify.
                value: One of 0, 1 or 2.
                    0: Set setting to False.
                    1: Set setting to True.
                    2: Set setting to value given in the commandline.
            """
            if options.contains(name):
                valuedict = {0: "false", 1: "true"}
                if value == 2:
                    valuedict[2] = options.lookup_value(name).unpack()
                settings.override(setting, valuedict[value])

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
            self._tmpdir = tempfile.TemporaryDirectory(prefix="vimiv-")
            tmp = self._tmpdir.name
            # Export environment variables for thumbnails, tags, history and
            # logs
            os.environ["XDG_CACHE_HOME"] = os.path.join(tmp, "cache")
            os.environ["XDG_CONFIG_HOME"] = os.path.join(tmp, "config")
            os.environ["XDG_DATA_HOME"] = os.path.join(tmp, "data")
        # Create settings as soon as we know which config files to use
        elif options.contains("config"):
            configfile = options.lookup_value("config").unpack()
            parse_config(commandline_config=configfile,
                         running_tests=self.running_tests)
        else:
            parse_config(running_tests=self.running_tests)

        # If we start from desktop, move to the wanted directory
        # Else if the input does not come from a tty, e.g. find "" | vimiv, set
        # paths and index according to the input from the pipe
        if options.contains("start-from-desktop"):
            os.chdir(settings["desktop_start_dir"].get_value())
        elif not sys.stdin.isatty():
            try:
                tty_paths = []
                for line in sys.stdin:
                    tty_paths.append(line.rstrip("\n"))
                self.populate(tty_paths)
            except TypeError:
                pass  # DebugConsoleStdIn is not iterable

        set_option("bar", "display_bar", 1)
        set_option("no-bar", "display_bar", 0)
        set_option("library", "show_library", 1)
        set_option("no-library", "show_library", 0)
        set_option("fullscreen", "start_fullscreen", 1)
        set_option("no-fullscreen", "start_fullscreen", 0)
        set_option("shuffle", "shuffle", 1)
        set_option("no-shuffle", "shuffle", 0)
        set_option("recursive", "recursive", 1)
        set_option("no-recursive", "recursive", 0)
        set_option("slideshow", "start_slideshow", 1)
        set_option("slideshow-delay", "slideshow_delay", 2)
        set_option("geometry", "geometry", 2)

        return -1  # To continue

    def activate_vimiv(self, app):
        """Starting point for the vimiv application.

        Args:
            app: The application itself.
        """
        self._init_widgets()
        self._create_window_structure()
        app.add_window(self["window"])
        # Show everything and then hide whatever needs to be hidden
        self["window"].show_all()
        self["manipulate"].hide()
        self["commandline"].hide()
        self["completions"].hide()
        # Statusbar depending on setting
        if not settings["display_bar"].get_value():
            self["statusbar"].hide()
        self["statusbar"].set_separator_height()
        # Try to generate imagelist recursively from the current directory if
        # recursive is given and no paths exist
        if settings["recursive"].get_value() and not self._paths:
            shuffle = settings["shuffle"].get_value()
            self.populate([os.getcwd()], True, shuffle)
        # Show the image if an imagelist exists
        if self._paths:
            self["image"].load()
            # Show library at the beginning?
            if not settings["show_library"].get_value():
                self["library"].grid.hide()
            self["main_window"].grab_focus()
            # Start in slideshow mode?
            if settings["start_slideshow"].get_value():
                self["slideshow"].toggle()
        else:
            # Slideshow without paths makes no sense
            self["slideshow"].running = False
            self["library"].focus()
            if settings["expand_lib"].get_value():
                self["main_window"].hide()

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
        self["transform"].apply()
        # Save the history
        self["commandline"].write_history()
        # Write to log
        self["log"].write_message("Exited", "time")
        # Cleanup tmpdir
        if self._tmpdir:
            self._tmpdir.cleanup()
        # Call Gtk.Application.quit()
        self.quit()

    def get_focused_widget(self):
        """Return the currently focused widget as string."""
        if self["library"].is_focus():
            return "lib"
        elif self["thumbnail"].is_focus():
            return "thu"
        elif self["manipulate"].is_visible():
            return "man"
        return "im"

    def get_pos(self, get_filename=False):
        """Get the current position in the focused widget.

        get_filename: If True return filename instead of position.

        Return:
            Current position as number or filename.
        """
        focused_widget = self.get_focused_widget()

        # Get position and name
        filelist = self._paths
        position = self._index
        if focused_widget == "lib":
            position = self["library"].get_position()
            filelist = self["library"].files
        elif focused_widget == "thu":
            position = self["thumbnail"].get_position()

        if get_filename:
            return filelist[position] if position < len(filelist) else ""
        return position

    def get_paths(self):
        return self._paths

    def get_index(self):
        return self._index

    def get_path(self):
        return self._paths[self._index]

    def update_index(self, diff):
        self._index = (self._index + diff) % len(self._paths)

    def remove_path(self, path):
        self._paths.remove(path)

    def populate(self, args, recursive=False, shuffle_paths=False,
                 expand_single=True):
        """Simple wrapper for fileactions.populate.

        Args:
            args: Paths given.
            recursive: If True search path recursively for images.
            shuffle_paths: If True shuffle found paths randomly.
            expand_single: If True, populate a complete filelist with images
                from the same directory as the single argument given.
        """
        self._paths, self._index = populate(
            args, recursive=recursive, shuffle_paths=shuffle_paths,
            expand_single=expand_single)

    def _init_commandline_options(self):
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

    def _init_widgets(self):
        """Create all the other widgets and add them to the class."""
        self["eventhandler"] = EventHandler(self)
        self["transform"] = Transform(self)
        self["commandline"] = CommandLine(self)
        self["tags"] = TagHandler(self)
        self["mark"] = Mark(self)
        self["fileextras"] = FileExtras(self)
        self["statusbar"] = Statusbar(self)
        self["completions"] = Completion(self)
        self["slideshow"] = Slideshow(self)
        self["main_window"] = MainWindow(self)
        self["image"] = self["main_window"].image
        self["thumbnail"] = self["main_window"].thumbnail
        self["library"] = Library(self)
        self["manipulate"] = Manipulate(self)
        self["information"] = Information()
        self["window"] = Window(self)
        # Generate completions as soon as commands exist
        self["commandline"].init_commands()
        self["completions"].generate_commandlist()
        self["log"] = Log(self)

    def _create_window_structure(self):
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

    def __getitem__(self, name):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to access.
        Return:
            The widget if it exists. None else.
        """
        if name in self._widgets:
            return self._widgets[name]
        return None

    def __setitem__(self, name, widget):
        """Convenience method to access widgets via self[name].

        Args:
            name: Name of the widget to add.
            item: The actual widget to which name will refer.
        """
        self._widgets[name] = widget


# Initiate signals for the Vimiv class
GObject.signal_new("widget-layout-changed", Vimiv, GObject.SIGNAL_RUN_LAST,
                   None, (GObject.TYPE_PYOBJECT,))
GObject.signal_new("paths-changed", Vimiv, GObject.SIGNAL_RUN_LAST,
                   None, (GObject.TYPE_PYOBJECT,))
