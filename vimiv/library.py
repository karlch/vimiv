# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Library part of vimiv."""

import os

from gi.repository import Gdk, Gtk
from vimiv.fileactions import is_image
from vimiv.helpers import listdir_wrapper, sizeof_fmt


class Library(Gtk.TreeView):
    """Library of vimiv.

    Includes the treeview with the library and all actions that apply to it.

    Attributes:
        expand: If True expand the library to window width if no images are
            shown.
        show_hidden: If True show hidden files.
        files: Files in the library.
        grid: Gtk.Grid containing the TreeView and the border.

        _app: The main vimiv application to interact with.
        _default_width: Setting for the default width of the library.
        _file_check_amount: Amount of files checked in a directory to display
            amount of images in it.
        _markup: Markup string used to highlight search results.
        _positions: Dictionary that stores position in directories.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(Library, self).__init__()
        self._app = app
        library = settings["LIBRARY"]

        # Settings
        self._positions = {}
        self._default_width = library["library_width"]
        self.expand = library["expand_lib"]
        border_width = library["border_width"]
        self._markup = library["markup"]
        self.show_hidden = library["show_hidden"]
        self._file_check_amount = library["file_check_amount"]

        # Defaults
        self.files = []

        # Grid with treeview and border
        self.grid = Gtk.Grid()
        # A simple border
        if border_width:
            border = Gtk.Separator()
            border.set_size_request(border_width, 1)
            self.grid.attach(border, 1, 0, 1, 1)
        # Pack everything
        self.set_size_request(self._default_width - border_width, 10)
        scrolled_win = Gtk.ScrolledWindow()
        scrolled_win.set_vexpand(True)
        scrolled_win.add(self)
        scrolled_win.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.grid.attach(scrolled_win, 0, 0, 1, 1)
        # Treeview
        self.set_enable_search(False)
        # Select file when row activated
        self.connect("row-activated", self.file_select, True)
        # Handle key events
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key_press_event",
                     self._app["eventhandler"].on_key_press, "LIBRARY")
        self.connect("button_press_event",
                     self._app["eventhandler"].on_click, "LIBRARY")
        # Add the columns
        for i, name in enumerate(["Num", "Name", "Size", "M"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(name, renderer, markup=i)
            if name == "Name":
                column.set_expand(True)
                column.set_max_width(20)
            self.append_column(column)
        # Set the liststore model
        self.set_model(self._liststore_create())
        # Set the hexpand property if requested in the configfile
        if not self._app.get_paths() and self.expand:
            self.set_hexpand(True)

        # Connect signals
        self._app.connect("paths-changed", self._on_paths_changed)
        self._app["mark"].connect("marks-changed", self._on_marks_changed)

    def toggle(self, update_image=True):
        """Toggle the library.

        Args:
            update_image: If True update the image shown. Always the case except
            for when running toggle after file_select(), as file_select() does
            this by itself.
        """
        if self.grid.is_visible():
            self[os.getcwd()] = self.files[self.get_position()]
            self.grid.hide()
            self.focus(False)
        else:
            self.grid.show()
            if not self._app.get_paths():
                # Hide the non existing image and expand if necessary
                self._app["main_window"].hide()
                if self.expand:
                    self.set_hexpand(True)
            else:  # Try to focus the current image in the library
                image = self._app.get_path()
                image_path = os.path.dirname(image)
                image_name = os.path.basename(image)
                if image_path == os.getcwd() and image_name in self.files:
                    self[os.getcwd()] = image_name
            # Stop the slideshow
            if self._app["slideshow"].running:
                self._app["slideshow"].toggle()
            self.focus(True)
            # Markings and other stuff might have changed
            self.reload(os.getcwd())
        self._app.emit("widget-layout-changed", self)

    def focus(self, focus_library=True):
        """Set or remove focus from the library.

        Args:
            focus_library: If True focus the library. Else unfocus it.
        """
        if focus_library:
            self.grab_focus()
            if not self.grid.is_visible():
                self.toggle()
        else:
            self._app["main_window"].grab_focus()
        # Update info for the current mode
        self._app["statusbar"].update_info()

    def file_select(self, treeview, path, column, close):
        """Show image or open directory for activated file in library.

        Args:
            treeview: The Gtk.TreeView which emitted the signal.
            path: Gtk.TreePath that was activated.
            column: Column that was activated.
            close: If True close the library when finished.
        """
        # Empty directory
        if not path:
            self._app["statusbar"].message("No file to select", "error")
            return
        count = path.get_indices()[0]
        fil = self.files[count]
        self[os.getcwd()] = fil
        if os.getcwd() == self._app["tags"].directory:
            self._tag_select(fil, close)
        elif os.path.isdir(fil):  # Open directory
            self.move_up(fil)
        else:
            self._image_select(fil, close)

    def _tag_select(self, tagname, close):
        # Also close if selected twice
        if tagname == self._app["tags"].last or close:
            self.toggle(update_image=False)
        self._app["tags"].load(tagname)

    def _image_select(self, basename, close):
        image = os.path.abspath(basename)
        # Close thumbnail
        if self._app["thumbnail"].toggled:
            self._app["thumbnail"].toggle()
            self.grab_focus()
        if self._app.get_paths() and image == self._app.get_path():
            close = True  # Close if file selected twice
        index = 0  # Catch directories to focus correctly
        for f in self.files:
            if f == basename:
                break
            elif os.path.isfile(f):
                index += 1
        # Repopulate
        visible_image = self._app.get_path() if self._app.get_paths() else ""
        self._app.populate([basename])
        if self._app.get_paths():
            self.set_hexpand(False)
            # Only load a new image if needed
            if visible_image != image:
                self._app["image"].move_index(
                    delta=index - self._app.get_index())
            # Close the library depending on key and repeat
            if close:
                self.toggle(update_image=False)
            self._app["main_window"].show()

    def move_up(self, directory="..", start=False):
        """Move up a directory or to a specific one in the library.

        Args:
            directory: Directory to move to. Defaults to parent.
            start: If True the function was called on startup and should not
                reload the library as it does not exist yet.
        """
        # Allow moving up multiple times if using .. as directory:
        if directory == "..":
            repeat = self._app["eventhandler"].num_receive()
            directory = "/".join(repeat * [".."])
        try:
            curdir = os.getcwd()
            os.chdir(directory)
            if not start:
                self.reload(os.getcwd(), curdir)
                self.focus()
        except (FileNotFoundError, PermissionError):
            self._app["statusbar"].message("Directory not accessible", "error")

    def reload(self, directory, last_directory="", search=False):
        """Reload the treeview.

        Args:
            directory: Directory of the library.
            last_directory: Directory that was last opened in the library.
            search: If True the reload request comes from a search
        """
        # Reset search positions
        if not search:
            self._app["commandline"].search_positions = []
        # Create model in new directory
        self.set_model(self._liststore_create())
        # Warn if there are no files in the directory
        if not self.files:
            self._app["statusbar"].message("Directory is empty", "warning")
            return
        # Check if there is a saved position
        self.move_pos(True, self[directory])
        # Check if the last directory is in the current one
        if os.path.basename(last_directory) in self.files:
            self.move_pos(True,
                          self.files.index(os.path.basename(last_directory)))

    def reload_names(self):
        """Only reload names of the treeview."""
        model = self.get_model()
        for i, name in enumerate(self.files):
            markup_string = name
            if os.path.islink(name):
                markup_string += "  →  " + os.path.realpath(name)
            if os.path.isdir(name):
                markup_string = "<b>" + markup_string + "</b>"
            if i in self._app["commandline"].search_positions:
                markup_string = self._markup + markup_string + "</span>"
            model[i][1] = markup_string

    def move_pos(self, forward=True, defined_pos=None):
        """Move to a specific position in the library.

        Defaults to moving to the last file. Can be used for the first file or
        any defined position.

        Args:
            forward: If True move forwards.
            defined_pos: If not empty defines the position to move to.
        """
        if not self.files:
            self._app["statusbar"].message("No position to go to", "error")
            return
        max_pos = len(self.files)
        # Direct call from scroll
        if isinstance(defined_pos, int):
            new_pos = defined_pos
        elif forward:
            new_pos = self._app["eventhandler"].num_receive(max_pos) - 1
        else:
            new_pos = self._app["eventhandler"].num_receive() - 1
        if new_pos < 0 or new_pos > max_pos:
            self._app["statusbar"].message("Unsupported index", "warning")
            return
        self.set_cursor(Gtk.TreePath(new_pos), None, False)
        self.scroll_to_cell(Gtk.TreePath(new_pos), None, True, 0.5, 0)
        # Clear the prefix
        self._app["eventhandler"].num_clear()

    def resize(self, inc=True, require_val=False, val=None):
        """Resize the library and update the image if necessary.

        Args:
            inc: If True increase the library size.
            require_val: If True require a specific value val for the size.
            val: Specific value for the new size.
        """
        width = self.get_size_request()[0]
        # Check if val is an acceptable integer
        if val and not val.isdigit():
            message = "Library width must be an integer"
            self._app["statusbar"].message(message, "error")
            return
        if require_val:
            val = int(val) if val else self._default_width
            width = val
        else:  # Grow/shrink by value
            step = self._app["eventhandler"].num_receive()
            val = int(val) if val else 20 * step
            if inc:
                width += val
            else:
                width -= val
        # Set some reasonable limits to the library size
        if width > self._app["window"].winsize[0] - 200:
            width = self._app["window"].winsize[0] - 200
        elif width < 100:
            width = 100
        self.set_size_request(width, 10)
        self._app.emit("widget-layout-changed", self)

    def toggle_hidden(self):
        """Toggle showing of hidden files."""
        self.show_hidden = not self.show_hidden
        self.reload(".")

    def scroll(self, direction):
        """Scroll the library viewer and call file_select if necessary.

        Args:
            direction: One of 'hjkl' defining the scroll direction.

        Return:
            True to deactivate default key-bindings for arrow keys.
        """
        # Handle the specific keys
        if direction == "h":  # Behave like ranger
            self[os.getcwd()] = self.files[self.get_position()]
            self.move_up()
        elif direction == "l":
            self.file_select(self, self.get_cursor()[0],
                             None, False)
        elif direction in ["j", "k"]:
            # Scroll the tree checking for a user step
            step = self._app["eventhandler"].num_receive()
            if direction == "j":
                new_pos = self.get_position() + step
                if new_pos >= len(self.get_model()):
                    new_pos = len(self.get_model()) - 1
            else:
                new_pos = self.get_position() - step
                if new_pos < 0:
                    new_pos = 0
            self.move_pos(True, new_pos)
        else:
            self._app["statusbar"].message(
                "Invalid scroll direction " + direction, "error")
        return True  # Deactivates default bindings (here for Arrows)

    def get_position(self):
        """Return focused position as integer."""
        path = self.get_cursor()[0]
        return path.get_indices()[0] if path else 0

    def _liststore_create(self):
        """Create the Gtk.ListStore containing information on supported files.

        Return:
            The created liststore containing
            [count, filename, filesize, markup_string].
        """
        liststore = Gtk.ListStore(int, str, str, str)
        self.files, filesize = self._filelist_create()
        # Remove unsupported files if one isn't in the tags directory
        if os.getcwd() != self._app["tags"].directory:
            self.files = [
                possible_file
                for possible_file in self.files
                if is_image(possible_file) or os.path.isdir(possible_file)]
        # Add all supported files
        for i, fil in enumerate(self.files):
            markup_string = fil
            size = filesize[fil]
            marked_string = ""
            if os.path.islink(fil):
                markup_string += "  →  " + os.path.realpath(fil)
            if os.path.abspath(fil) in self._app["mark"].marked:
                marked_string = "[*]"
            if os.path.isdir(fil):
                markup_string = "<b>" + markup_string + "</b>"
            if i in self._app["commandline"].search_positions:
                markup_string = self._markup + markup_string + "</span>"
            liststore.append([i + 1, markup_string, size, marked_string])

        return liststore

    def _filelist_create(self, directory="."):
        """Create a filelist from all files in directory.

        Args:
            directory: Directory of which the filelist is created.
        Return:
            filelist, filesize: List of files, dictionary with filesize info
        """
        # Get data from ls -lh and parse it correctly
        files = listdir_wrapper(directory, self.show_hidden)
        filesize = {}
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
                    if len(subfiles) > self._file_check_amount:
                        many = True
                    subfiles = [sub
                                for sub in subfiles[:self._file_check_amount]
                                if is_image(os.path.join(fil, sub))]
                    amount = str(len(subfiles))
                    if subfiles and many:
                        amount += "+"
                    filesize[fil] = amount
                except PermissionError:
                    filesize[fil] = "N/A"
            else:
                filesize[fil] = sizeof_fmt(os.path.getsize(fil))

        return files, filesize

    def _on_paths_changed(self, app, widget):
        """Reload filelist on the paths-changed signal from app."""
        # Expand library if set by user and all paths were removed
        if not self._app.get_paths() and self.expand:
            self.set_hexpand(True)
            if not self.is_focus():
                self.focus()
        if self.grid.is_visible():
            # Reload remembering path
            self[os.getcwd()] = self.files[self.get_position()]
            self.reload(os.getcwd())

    def _on_marks_changed(self, mark, changed):
        """Reload names if marks changed."""
        if self.grid.is_visible():
            model = self.get_model()
            for i, name in enumerate(self.files):
                model[i][3] = "[*]" \
                    if os.path.abspath(name) in mark.marked else ""

    def __getitem__(self, directory):
        """Convenience method to access saved positions via self[directory].

        Args:
            directory: Name of the directory to search for a saved position.
        Return:
            The index of the saved file if any.
        """
        if directory in self._positions:
            filename = self._positions[directory]
            if filename in self.files:
                return self.files.index(filename)
        return 0

    def __setitem__(self, directory, filename):
        """Convenience method to save positions in via self[directory].

        Args:
            directory: Name of the directory to search for a saved position.
            filename: Name of the file to save.
        """
        self._positions[directory] = filename
