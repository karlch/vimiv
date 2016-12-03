#!/usr/bin/env python
# encoding: utf-8
"""Library part of self.vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv.fileactions import is_image, populate
from vimiv.helpers import listdir_wrapper, sizeof_fmt


class Library(object):
    """Library of vimiv.

    Includes the treeview with the library and all actions that apply to it

    Attributes:
        vimiv: The main vimiv class to interact with.
        dir_pos: Dictionary that stores position in directories.
        show_at_start: If True show library at startup.
        default_width: Setting for the default width of the library.
        expand: If True expand the library to window width if no images are
            shown.
        width: Width of the actual library without border width.
        markup: Markup string used to highlight search results.
        show_hidden: If True show hidden files.
        file_check_amount: Amount of files checked in a directory to display
            amount of images in it.
        desktop_start_dir: Directory to start in if launched from desktop.
        files: Files in the library.
        datalist: List containing information on files (formatted name, size,
            mark indicator).
        filesize: Dictionary storing the size of files.
        file_liststore: Gtk.ListStore for the file information to be displayed.
        grid: Gtk.Grid containing the TreeView and the border.
        scrollable_treeview: Gtk.ScrolledWindow in which the TreeView gets
            packed.
        treeview: Gtk.TreeView object with file_liststore as model.
    """

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv
        library = settings["LIBRARY"]

        # Settings
        self.dir_pos = {}  # Remembers positions in the library browser
        self.show_at_start = library["show_library"]
        self.default_width = library["library_width"]
        self.expand = library["expand_lib"]
        border_width = library["border_width"]
        self.width = self.default_width - border_width
        self.markup = library["markup"]
        self.show_hidden = library["show_hidden"]
        self.file_check_amount = library["file_check_amount"]
        self.desktop_start_dir = library["desktop_start_dir"]

        # Defaults
        self.files = []
        self.datalist = []
        self.filesize = {}
        # Filelist in a liststore model
        self.file_liststore = Gtk.ListStore(int, str, str, str)

        # Grid with treeview and border
        self.grid = Gtk.Grid()
        # A simple border
        if border_width:
            border = Gtk.Separator()
            border.set_size_request(border_width, 1)
            self.grid.attach(border, 1, 0, 1, 1)
        # Pack everything
        self.scrollable_treeview = Gtk.ScrolledWindow()
        self.scrollable_treeview.set_vexpand(True)
        self.scrollable_treeview.set_size_request(self.width, 10)
        self.grid.attach(self.scrollable_treeview, 0, 0, 1, 1)
        # Treeview
        self.treeview = Gtk.TreeView()
        self.scrollable_treeview.add(self.treeview)
        self.treeview.set_enable_search(False)
        # Select file when row activated
        self.treeview.connect("row-activated", self.file_select, True)
        # Handle key events
        self.treeview.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.treeview.connect("key_press_event",
                              self.vimiv.keyhandler.run, "LIBRARY")
        # Call the function to create the treeview
        self.update_treeview()
        # Set the hexpand property if requested in the configfile
        if (not self.vimiv.paths or isinstance(self.vimiv.paths, str)) \
                and self.expand:
            self.treeview.set_hexpand(True)

    def toggle(self, update_image=True):
        """Toggle the library.

        Args:
            update_image: If True update the image shown. Always the case except
            for when running toggle after file_select(), as file_select() does
            this by itself.
        """
        if self.grid.is_visible():
            self.remember_pos(os.getcwd(),
                              self.vimiv.get_pos(force_widget="lib"))
            self.grid.hide()
            self.focus(False)
        else:
            self.grid.show()
            if not self.vimiv.paths:
                # Hide the non existing image and expand if necessary
                self.vimiv.image.vimiv.image.scrolled_win.hide()
                if self.expand:
                    self.scrollable_treeview.set_hexpand(True)
            else:  # Try to focus the current image in the library
                image = self.vimiv.paths[self.vimiv.index]
                image_path = os.path.dirname(image)
                image_name = os.path.basename(image)
                if image_path == os.getcwd():
                    for i, fil in enumerate(self.files):
                        if fil == image_name:
                            self.remember_pos(os.getcwd(), i)
                            break
            # Stop the slideshow
            if self.vimiv.slideshow.running:
                self.vimiv.slideshow.toggle()
            self.focus(True)
            # Markings and other stuff might have changed
            self.reload(os.getcwd())
        # Resize image and grid if necessary
        if self.vimiv.paths and update_image:
            if self.vimiv.thumbnail.toggled:
                self.vimiv.thumbnail.calculate_columns()
            elif not self.vimiv.image.user_zoomed:
                self.vimiv.image.zoom_to(0)
            else:
                #  Change the toggle state of animation
                self.vimiv.image.update()

    def focus(self, focus_library=True):
        """Set or remove focus from the library.

        Args:
            focus_library: If True focus the library. Else unfocus it.
        """
        if focus_library:
            self.treeview.grab_focus()
            if not self.grid.is_visible():
                self.toggle()
        else:
            self.vimiv.image.vimiv.image.scrolled_win.grab_focus()
        # Update info for the current mode
        self.vimiv.statusbar.update_info()

    def update_treeview(self, search=False):
        """Renew the information in the treeview.

        Args:
            search: If True a search was performed. Necessary to highlight
            search results and delete search items if a new directory is
            entered.
        """
        if not search:
            self.vimiv.commandline.search_positions = []
        # Remove old columns
        for column in self.treeview.get_columns():
            self.treeview.remove_column(column)
        # Tree View
        current_file_filter = self.file_filter_create(self.datalist_create())
        self.treeview.set_model(current_file_filter)
        # Add the columns
        for i, name in enumerate(["Num", "Name", "Size", "M"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(name, renderer, markup=i)
            if name == "Name":
                column.set_expand(True)
                column.set_max_width(20)
            self.treeview.append_column(column)

    def file_filter_create(self, datalist):
        """Create the file_filter for the treeview.

        Args:
            datalist:

        Return: Gtk.ListStore.filter_new to use as treeview model.
        """
        # Reset
        self.file_liststore = Gtk.ListStore(int, str, str, str)
        # Numerate each filename
        count = 0
        for data in datalist:
            count += 1
            data.insert(0, count)
            # The data into the filelist
            self.file_liststore.append(data)

        current_file_filter = self.file_liststore.filter_new()
        return current_file_filter

    def datalist_create(self):
        """Create the list of data for the file_filter model.

        Return: The created datalist.
        """
        self.datalist = []
        self.files = self.filelist_create()
        # Remove unsupported files if one isn't in the tags directory
        if os.getcwd() != self.vimiv.tags.directory:
            self.files = [
                possible_file
                for possible_file in self.files
                if is_image(possible_file) or os.path.isdir(possible_file)]
        # Add all supported files
        for i, fil in enumerate(self.files):
            markup_string = fil
            size = self.filesize[fil]
            is_marked = ""
            if os.path.islink(fil):
                markup_string = markup_string + "  →  " + os.path.realpath(fil)
            if os.path.abspath(fil) in self.vimiv.mark.marked:
                is_marked = "[*]"
            if os.path.isdir(fil):
                markup_string = "<b>" + markup_string + "</b>"
            if i in self.vimiv.commandline.search_positions:
                markup_string = self.markup + markup_string + '</span>'
            self.datalist.append([markup_string, size, is_marked])

        return self.datalist

    def file_select(self, treeview, path, column, close):
        """Show image or open directory for activated file in library.

        Args:
            treeview: The Gtk.TreeView which emitted the signal.
            path: Gtk.TreePath that was activated.
            column: Column that was activated.
            close: If True close the library when finished.
        """
        count = path.get_indices()[0]
        fil = self.files[count]
        self.remember_pos(os.getcwd(), count)
        # Tags
        if os.getcwd() == self.vimiv.tags.directory:
            # Close if selected twice
            if fil == self.vimiv.tags.last:
                self.toggle()
            self.vimiv.tags.load(fil)
            return
        # Rest
        if os.path.isdir(fil):  # Open the directory
            self.move_up(fil)
        else:  # Focus the image and populate a new list from the dir
            # If thumbnail toggled, go out
            if self.vimiv.thumbnail.toggled:
                self.vimiv.thumbnail.toggle()
                self.treeview.grab_focus()
            if self.vimiv.paths and fil in self.vimiv.paths[self.vimiv.index]:
                close = True  # Close if file selected twice
            index = 0  # Catch directories to focus correctly
            for f in self.files:
                if f == fil:
                    break
                elif os.path.isfile(f):
                    index += 1
            self.vimiv.paths, self.vimiv.index = populate(self.files)
            if self.vimiv.paths:
                self.scrollable_treeview.set_hexpand(False)
                self.vimiv.image.scrolled_win.show()
                # Close the library depending on key and repeat
                if close:
                    # We do not need to update the image as it is done later
                    # anyway
                    self.toggle(update_image=False)
                self.vimiv.image.move_index(delta=index)

    def move_up(self, directory="..", start=False):
        """Move up a directory or to a specific one in the library.

        Args:
            directory: Directory to move to. Defaults to parent.
            start: If True the function was called on startup and should not
                reload the library as it does not exist yet.
        """
        try:
            curdir = os.getcwd()
            os.chdir(directory)
            if not start:
                self.reload(os.getcwd(), curdir)
        except:
            self.vimiv.statusbar.err_message("Error: directory not accessible")

    def remember_pos(self, directory, position):
        """Write the current position in directory to the dir_pos dictionary.

        Args:
            directory: Directory of which to remember the position.
            position: Current position in library.
        """
        self.dir_pos[directory] = position

    def reload(self, directory, last_directory="", search=False):
        """Reload the treeview.

        Args:
            directory: Directory of the library.
            last_directory: Directory that was last opened in the library.
            search: If True the reload request comes from a search
        """
        self.update_treeview(search)
        self.focus(True)
        # Check if there is a saved position
        if directory in self.dir_pos.keys():
            self.move_pos(True, self.dir_pos[directory])
        # Check if the last directory is in the current one
        else:
            for i, fil in enumerate(self.files):
                if os.path.basename(last_directory) == fil:
                    self.move_pos(True, i)
                    break

    def move_pos(self, forward=True, defined_pos=None):
        """Move to a specific position in the library.

        Defaults to moving to the last file. Can be used for the first file or
        any defined position.

        Args:
            forward: If True move forwards.
            defined_pos: If not empty defines the position to move to.
        """
        if not self.files:
            self.vimiv.statusbar.err_message("Warning: Directory is empty")
            return
        max_pos = len(self.files) - 1
        # Direct call from scroll
        if isinstance(defined_pos, int):
            new_pos = defined_pos
        # Call from g/G via key-binding
        elif self.vimiv.keyhandler.num_str:
            new_pos = int(self.vimiv.keyhandler.num_str) - 1
            self.vimiv.keyhandler.num_clear()
            if new_pos < 0 or new_pos > max_pos:
                self.vimiv.statusbar.err_message("Warning: Unsupported index")
                return
        elif forward:
            new_pos = max_pos
        else:
            new_pos = 0
        self.treeview.set_cursor(Gtk.TreePath(new_pos), None, False)
        self.treeview.scroll_to_cell(Gtk.TreePath(new_pos), None, True,
                                     0.5, 0)
        # Clear the prefix
        self.vimiv.keyhandler.num_clear()

    def resize(self, inc=True, require_val=False, val=None):
        """Resize the library and update the image if necessary.

        Args:
            inc: If True increase the library size.
            require_val: If True require a specific value val for the size.
            val: Specific value for the new size.
        """
        if require_val:  # Set to value
            if not val:
                val = self.default_width
            try:
                val = int(val)
            except:
                message = "Library width must be an integer"
                self.vimiv.statusbar.err_message(message)
                return
            self.width = val
        else:  # Grow/shrink by value
            if not val:
                val = 20
            try:
                val = int(val)
            except:
                message = "Library width must be an integer"
                self.vimiv.statusbar.err_message(message)
                return
            if inc:
                self.width += val
            else:
                self.width -= val
        # Set some reasonable limits to the library size
        if self.width > self.vimiv.winsize[0] - 200:
            self.width = self.vimiv.winsize[0] - 200
        elif self.width < 100:
            self.width = 100
        self.scrollable_treeview.set_size_request(self.width, 10)
        # Rezoom image
        if not self.vimiv.image.user_zoomed and self.vimiv.paths:
            self.vimiv.image.zoom_to(0)

    def toggle_hidden(self):
        """Toggle showing of hidden files."""
        self.show_hidden = not self.show_hidden
        self.reload('.')

    def filelist_create(self, directory="."):
        """Create a filelist from all files in directory.

        Args:
            directory: Directory of which the filelist is created.
        """
        # Get data from ls -lh and parse it correctly
        files = listdir_wrapper(directory, self.show_hidden)
        self.filesize = {}
        for fil in files:
            # Catch broken symbolic links
            if os.path.islink(fil) and \
                    not os.path.exists(os.path.realpath(fil)):
                continue
            # Number of images in directory as filesize
            if os.path.isdir(fil):
                try:
                    subfiles = listdir_wrapper(fil, self.show_hidden)
                    # Necessary to keep acceptable speed in library
                    many = False
                    if len(subfiles) > self.file_check_amount:
                        many = True
                    subfiles = [subfile
                                for subfile in subfiles[:self.file_check_amount]
                                if is_image(os.path.join(fil, subfile))]
                    amount = str(len(subfiles))
                    if subfiles and many:
                        amount += "+"
                    self.filesize[fil] = amount
                except:
                    self.filesize[fil] = "N/A"
            else:
                self.filesize[fil] = sizeof_fmt(os.path.getsize(fil))

        return files

    def scroll(self, direction):
        """Scroll the library viewer and call file_select if necessary.

        Args:
            direction: One of 'hjkl' defining the scroll direction.

        Return: True to deactivate default key-bindings for arrow keys.
        """
        # Handle the specific keys
        if direction == "h":  # Behave like ranger
            self.remember_pos(os.getcwd(),
                              self.vimiv.get_pos(force_widget="lib"))
            self.move_up()
        elif direction == "l":
            self.file_select(self.treeview, self.treeview.get_cursor()[0],
                             None, False)
        else:
            # Scroll the tree checking for a user step
            if self.vimiv.keyhandler.num_str:
                step = int(self.vimiv.keyhandler.num_str)
            else:
                step = 1
            if direction == "j":
                new_pos = self.vimiv.get_pos(force_widget="lib") + step
                if new_pos >= len(self.file_liststore):
                    new_pos = len(self.file_liststore) - 1
            else:
                new_pos = self.vimiv.get_pos(force_widget="lib") - step
                if new_pos < 0:
                    new_pos = 0
            self.move_pos(True, new_pos)
        return True  # Deactivates default bindings (here for Arrows)
