# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Library part of self.app."""

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
        app: The main vimiv application to interact with.
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
        tilde_in_statusbar: If True, collapse $HOME to ~ in statusbar.
        files: Files in the library.
        filesize: Dictionary storing the size of files.
        grid: Gtk.Grid containing the TreeView and the border.
        scrollable_treeview: Gtk.ScrolledWindow in which the TreeView gets
            packed.
        treeview: Gtk.TreeView object with own liststore model containing
            number, filename, filesize and is_marked.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        self.app = app
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
        self.tilde_in_statusbar = library["tilde_in_statusbar"]

        # Defaults
        self.files = []
        self.filesize = {}

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
                              self.app["keyhandler"].run, "LIBRARY")
        # Add the columns
        for i, name in enumerate(["Num", "Name", "Size", "M"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(name, renderer, markup=i)
            if name == "Name":
                column.set_expand(True)
                column.set_max_width(20)
            self.treeview.append_column(column)
        # Set the liststore model
        self.treeview.set_model(self.liststore_create())
        # Set the hexpand property if requested in the configfile
        if not self.app.paths and self.expand:
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
                              self.app.get_pos(force_widget="lib"))
            self.grid.hide()
            self.focus(False)
        else:
            self.grid.show()
            if not self.app.paths:
                # Hide the non existing image and expand if necessary
                self.app["image"].scrolled_win.hide()
                if self.expand:
                    self.scrollable_treeview.set_hexpand(True)
            else:  # Try to focus the current image in the library
                image = self.app.paths[self.app.index]
                image_path = os.path.dirname(image)
                image_name = os.path.basename(image)
                if image_path == os.getcwd() and image_name in self.files:
                    self.remember_pos(os.getcwd(), self.files.index(image_name))
            # Stop the slideshow
            if self.app["slideshow"].running:
                self.app["slideshow"].toggle()
            self.focus(True)
            # Markings and other stuff might have changed
            self.reload(os.getcwd())
        # Resize image and grid if necessary
        if self.app.paths and update_image:
            if self.app["thumbnail"].toggled:
                self.app["thumbnail"].calculate_columns()
            elif self.app["image"].fit_image and \
                    not self.app["image"].is_anim:
                self.app["image"].zoom_to(0, self.app["image"].fit_image)
            else:
                #  Change the toggle state of animation
                self.app["image"].update()

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
            self.app["image"].scrolled_win.grab_focus()
        # Update info for the current mode
        self.app["statusbar"].update_info()

    def liststore_create(self):
        """Create the Gtk.ListStore containing information on supported files.

        Return:
            The created liststore containing
            [count, filename, filesize, markup_string].
        """
        liststore = Gtk.ListStore(int, str, str, str)
        self.files = self.filelist_create()
        # Remove unsupported files if one isn't in the tags directory
        if os.getcwd() != self.app["tags"].directory:
            self.files = [
                possible_file
                for possible_file in self.files
                if is_image(possible_file) or os.path.isdir(possible_file)]
        # Add all supported files
        for i, fil in enumerate(self.files):
            markup_string = fil
            size = self.filesize[fil]
            marked_string = ""
            if os.path.islink(fil):
                markup_string = markup_string + "  →  " + os.path.realpath(fil)
            if os.path.abspath(fil) in self.app["mark"].marked:
                marked_string = "[*]"
            if os.path.isdir(fil):
                markup_string = "<b>" + markup_string + "</b>"
            if i in self.app["commandline"].search_positions:
                markup_string = self.markup + markup_string + '</span>'
            liststore.append([i + 1, markup_string, size, marked_string])

        return liststore

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
            self.app["statusbar"].message("No file to select", "error")
            return
        count = path.get_indices()[0]
        fil = self.files[count]
        self.remember_pos(os.getcwd(), count)
        # Tags
        if os.getcwd() == self.app["tags"].directory:
            # Close if selected twice
            if fil == self.app["tags"].last:
                self.toggle()
            self.app["tags"].load(fil)
            return
        # Rest
        if os.path.isdir(fil):  # Open the directory
            self.move_up(fil)
        else:  # Focus the image and populate a new list from the dir
            # If thumbnail toggled, go out
            if self.app["thumbnail"].toggled:
                self.app["thumbnail"].toggle()
                self.treeview.grab_focus()
            if self.app.paths and fil in self.app.paths[self.app.index]:
                close = True  # Close if file selected twice
            index = 0  # Catch directories to focus correctly
            for f in self.files:
                if f == fil:
                    break
                elif os.path.isfile(f):
                    index += 1
            self.app.paths, self.app.index = populate(self.files)
            if self.app.paths:
                self.scrollable_treeview.set_hexpand(False)
                self.app["image"].scrolled_win.show()
                # Close the library depending on key and repeat
                if close:
                    # We do not need to update the image as it is done later
                    # anyway
                    self.toggle(update_image=False)
                self.app["image"].move_index(delta=index)

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
        except (FileNotFoundError, PermissionError):
            self.app["statusbar"].message("Directory not accessible", "error")

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
        # Reset search positions
        if not search:
            self.app["commandline"].search_positions = []
        # Create model in new directory
        self.treeview.set_model(self.liststore_create())
        self.focus(True)
        # Warn if there are no files in the directory
        if not self.files:
            self.app["statusbar"].message("Directory is empty", "warning")
            return
        # Check if there is a saved position
        if directory in self.dir_pos:
            self.move_pos(True, self.dir_pos[directory])
        # Check if the last directory is in the current one
        elif os.path.basename(last_directory) in self.files:
            self.move_pos(True,
                          self.files.index(os.path.basename(last_directory)))

    def reload_names(self):
        """Only reload names of the treeview."""
        model = self.treeview.get_model()
        for i, name in enumerate(self.files):
            markup_string = "<b>" + name + "</b>" \
                if os.path.isdir(name) \
                else name
            if i in self.app["commandline"].search_positions:
                markup_string = self.markup + markup_string + "</span>"
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
            self.app["statusbar"].message("No position to go to", "error")
            return
        max_pos = len(self.files) - 1
        # Direct call from scroll
        if isinstance(defined_pos, int):
            new_pos = defined_pos
        # Call from g/G via key-binding
        elif self.app["keyhandler"].num_str:
            new_pos = int(self.app["keyhandler"].num_str) - 1
            self.app["keyhandler"].num_clear()
            if new_pos < 0 or new_pos > max_pos:
                self.app["statusbar"].message("Unsupported index", "warning")
                return
        elif forward:
            new_pos = max_pos
        else:
            new_pos = 0
        self.treeview.set_cursor(Gtk.TreePath(new_pos), None, False)
        self.treeview.scroll_to_cell(Gtk.TreePath(new_pos), None, True,
                                     0.5, 0)
        # Clear the prefix
        self.app["keyhandler"].num_clear()

    def resize(self, inc=True, require_val=False, val=None):
        """Resize the library and update the image if necessary.

        Args:
            inc: If True increase the library size.
            require_val: If True require a specific value val for the size.
            val: Specific value for the new size.
        """
        # Check if val is an acceptable integer
        if val and not val.isdigit():
            message = "Library width must be an integer"
            self.app["statusbar"].message(message, "error")
            return
        if require_val:
            val = int(val) if val else self.default_width
            self.width = val
        else:  # Grow/shrink by value
            val = int(val) if val else 20
            if inc:
                self.width += val
            else:
                self.width -= val
        # Set some reasonable limits to the library size
        if self.width > self.app["window"].winsize[0] - 200:
            self.width = self.app["window"].winsize[0] - 200
        elif self.width < 100:
            self.width = 100
        self.scrollable_treeview.set_size_request(self.width, 10)
        # Rezoom image
        if self.app["image"].fit_image and self.app.paths and \
                not self.app["image"].is_anim:
            self.app["image"].zoom_to(0, self.app["image"].fit_image)

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
                except PermissionError:
                    self.filesize[fil] = "N/A"
            else:
                self.filesize[fil] = sizeof_fmt(os.path.getsize(fil))

        return files

    def scroll(self, direction):
        """Scroll the library viewer and call file_select if necessary.

        Args:
            direction: One of 'hjkl' defining the scroll direction.

        Return:
            True to deactivate default key-bindings for arrow keys.
        """
        # Handle the specific keys
        if direction == "h":  # Behave like ranger
            self.remember_pos(os.getcwd(),
                              self.app.get_pos(force_widget="lib"))
            self.move_up()
        elif direction == "l":
            self.file_select(self.treeview, self.treeview.get_cursor()[0],
                             None, False)
        elif direction in ["j", "k"]:
            # Scroll the tree checking for a user step
            step = int(self.app["keyhandler"].num_str) \
                if self.app["keyhandler"].num_str \
                else 1
            if direction == "j":
                new_pos = self.app.get_pos(force_widget="lib") + step
                if new_pos >= len(self.treeview.get_model()):
                    new_pos = len(self.treeview.get_model()) - 1
            else:
                new_pos = self.app.get_pos(force_widget="lib") - step
                if new_pos < 0:
                    new_pos = 0
            self.move_pos(True, new_pos)
        else:
            self.app["statusbar"].message(
                "Invalid scroll direction " + direction, "error")
        return True  # Deactivates default bindings (here for Arrows)
