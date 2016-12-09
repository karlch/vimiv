#!/usr/bin/env python
# encoding: utf-8

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio
from vimiv.image import Image
from vimiv.fileactions import FileExtras
from vimiv.library import Library
from vimiv.thumbnail import Thumbnail
from vimiv.manipulate import Manipulate
from vimiv.statusbar import Statusbar
from vimiv.commandline import CommandLine
from vimiv.commands import Commands
from vimiv.completions import VimivComplete
from vimiv.slideshow import Slideshow
from vimiv.events import KeyHandler
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

    def __init__(self, application_id):
        """Create the Gtk.Application and connect the activate signal.

        Args:
            application_id: The ID used to register vimiv. Default: org.vimiv.
        """
        Gtk.Application.__init__(self, application_id=application_id,
                                 flags=Gio.ApplicationFlags.SEND_ENVIRONMENT)
        self.connect("activate", self.activate)
        self.settings = {}
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

    def activate(self, app):
        """Starting point for the vimiv application.

        Args:
            app: The application itself.
        """
        self.init_widgets()
        self.create_window_structure()
        app.add_window(self["window"])
        # Move to the directory of the image
        # TODO using isinstance is ugly
        if self.paths:
            if isinstance(self.paths, list):
                os.chdir(os.path.dirname(self.paths[self.index]))
            else:
                os.chdir(self.paths)
                self.paths = []

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
            self["statusbar"].err_message("No valid paths, opening library viewer")

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
