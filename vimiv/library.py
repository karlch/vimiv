#!/usr/bin/env python
# encoding: utf-8
""" Library part of self.vimiv """

import os
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from vimiv.fileactions import is_image, populate
from vimiv.helpers import listdir_wrapper


class Library(object):
    """ Library class for self.vimiv
        includes the treeview with the library and all actions that apply to
        it """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        library = settings["LIBRARY"]

        # Settings
        self.dir_pos = {}  # Remembers positions in the library browser
        self.toggled = library["show_library"]
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
        self.treepos = 0
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
        # Resize accordingly
        if self.vimiv.paths or not self.expand:
            self.scrollable_treeview.set_size_request(self.width, 10)
        else:
            self.scrollable_treeview.set_size_request(self.vimiv.winsize[0], 10)

    def toggle(self):
        """ Toggles the library """
        if self.toggled:
            self.remember_pos(os.getcwd(), self.treepos)
            self.grid.hide()
            self.vimiv.image.animation_toggled = False  # Now play Gifs
            self.toggled = not self.toggled
            self.focus(False)
        else:
            self.grid.show()
            if not self.vimiv.paths:
                # Hide the non existing image and expand if necessary
                self.vimiv.image.vimiv.image.scrolled_win.hide()
                if self.expand:
                    self.scrollable_treeview.set_size_request(
                        self.vimiv.winsize[0], 10)
            else:  # Try to focus the current image in the library
                image = self.vimiv.paths[self.vimiv.index]
                image_path = os.path.dirname(image)
                image_name = os.path.basename(image)
                if image_path == os.getcwd():
                    for i, fil in enumerate(self.files):
                        if fil == image_name:
                            self.remember_pos(os.getcwd(), i)
                            break
            # Do not play Gifs with the lib
            self.vimiv.image.animation_toggled = True
            self.toggled = not self.toggled
            self.focus(True)
            # Markings and other stuff might have changed
            self.reload(os.getcwd())
        # Resize image and grid if necessary
        if self.vimiv.paths:
            if self.vimiv.thumbnail.toggled:
                self.vimiv.thumbnail.calculate_columns()
            if not self.vimiv.image.user_zoomed:
                self.vimiv.image.zoom_to(0)
        #  Change the toggle state of animation
        self.vimiv.image.update()

    def focus(self, library=True):
        """ Focused library object """
        if library:
            if not self.toggled:
                self.toggle()
            self.treeview.grab_focus()
        else:
            self.vimiv.image.vimiv.image.scrolled_win.grab_focus()
        # Update info for the current mode
        self.vimiv.statusbar.update_info()

    def update_treeview(self, search=False):
        """ Renews the information in the treeview """
        # The search parameter is necessary to highlight searches after a search
        # and to delete search items if a new directory is entered
        if not search:
            self.vimiv.commandline.reset_search()
        # Remove old columns
        for column in self.treeview.get_columns():
            self.treeview.remove_column(column)
        # Tree View
        current_file_filter = self.filestore(self.datalist_create())
        self.treeview.set_model(current_file_filter)
        # Needed for the movement keys
        self.treepos = 0
        # Add the columns
        for i, name in enumerate(["Num", "Name", "Size", "M"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(name, renderer, markup=i)
            if name == "Name":
                column.set_expand(True)
                column.set_max_width(20)
            self.treeview.append_column(column)

    def filestore(self, datalist):
        """ Returns the file_filter for the tree view """
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
        """ Returns the list of data for the file_filter model """
        self.datalist = list()
        self.files = self.filelist_create()
        # Remove unsupported files if one isn't in the self.vimiv.tags.directory
        if os.getcwd() != self.vimiv.tags.directory:
            self.files = [
                possible_file
                for possible_file in self.files
                if is_image(possible_file) or os.path.isdir(possible_file)]
        # Add all the supported files
        for fil in self.files:
            markup_string = fil
            size = self.filesize[fil]
            is_marked = ""
            if os.path.islink(fil):
                markup_string = markup_string + "  →  " + os.path.realpath(fil)
            if os.path.abspath(fil) in self.vimiv.mark.marked:
                is_marked = "[*]"
            if os.path.isdir(fil):
                markup_string = "<b>" + markup_string + "</b>"
            if fil in self.vimiv.commandline.search_names:
                markup_string = self.markup + markup_string + '</span>'
            self.datalist.append([markup_string, size, is_marked])

        return self.datalist

    def file_select(self, alternative, count, b, close):
        """ Focus image or open dir for activated file in library """
        if isinstance(count, str):
            fil = count
        else:
            count = count.get_indices()[0]
            fil = self.files[count]
            self.remember_pos(os.getcwd(), count)
        # Tags
        if os.getcwd() == self.vimiv.tags.directory:
            self.vimiv.tags.load(fil)
            # Close if selected twice
            if fil == self.vimiv.tags.last:
                self.toggle()
            # Remember last tag selected
            self.vimiv.tags.last = fil
            return
        # Rest
        if os.path.isdir(fil):  # Open the directory
            self.move_up(fil)
        else:  # Focus the image and populate a new list from the dir
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
                self.scrollable_treeview.set_size_request(self.width, 10)
                self.vimiv.image.scrolled_win.show()
            # Show the selected file, if thumbnail toggled go out
            if self.vimiv.thumbnail.toggled:
                self.vimiv.thumbnail.toggle()
                self.treeview.grab_focus()
            self.vimiv.image.move_index(delta=index)
            # Close the library depending on key and repeat
            if close:
                self.toggle()
                self.vimiv.image.update()

    def move_up(self, directory="..", start=False):
        """ move (up/to) directory in the library """
        try:
            curdir = os.getcwd()
            os.chdir(directory)
            if not start:
                self.reload(os.getcwd(), curdir)
        except:
            self.vimiv.statusbar.err_message("Error: directory not accessible")

    def remember_pos(self, directory, count):
        """ Write the current position in dir to the dir_pos dictionary """
        self.dir_pos[directory] = count

    def reload(self, directory, curdir="", search=False):
        """ Reloads the treeview """
        self.update_treeview(search)
        self.focus(True)
        # Check if there is a saved position
        if directory in self.dir_pos.keys():
            self.move_pos(True, self.dir_pos[directory])
        # Check if the last directory is in the current one
        else:
            last_dir = os.path.basename(curdir)
            for i, fil in enumerate(self.files):
                if last_dir == fil:
                    self.move_pos(True, i)
                    break
        self.grid.show_all()

    def move_pos(self, forward=True, defined_pos=None):
        """ Move to pos in lib """
        if not self.files:
            self.vimiv.statusbar.err_message("Directory is empty")
            return
        max_pos = len(self.files) - 1
        # Direct call from scroll
        if isinstance(defined_pos, int):
            new_pos = defined_pos
        # Call from g/G via keybinding
        elif self.vimiv.keyhandler.num_str:
            new_pos = int(self.vimiv.keyhandler.num_str) - 1
            if new_pos < 0 or new_pos > max_pos:
                self.vimiv.statusbar.err_message("Warning: Unsupported index")
                return False
        elif forward:
            new_pos = max_pos
        else:
            new_pos = 0
        self.treeview.set_cursor(Gtk.TreePath(new_pos), None, False)
        self.treeview.scroll_to_cell(Gtk.TreePath(new_pos), None, True,
                                     0.5, 0)
        self.treepos = new_pos
        # Clear the prefix
        self.vimiv.keyhandler.num_clear()
        return True

    def resize(self, inc=True, require_val=False, val=None):
        """ Resize the library and update the image if necessary """
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
        """ Toggles showing of hidden files """
        self.show_hidden = not self.show_hidden
        self.reload('.')

    def filelist_create(self, directory="."):
        """ Create a filelist from all files in directory """
        # Get data from ls -lh and parse it correctly
        if self.show_hidden:
            p = Popen(['ls', '-lAhL', directory], stdin=PIPE, stdout=PIPE,
                      stderr=PIPE)
        else:
            p = Popen(['ls', '-lhL', directory], stdin=PIPE, stdout=PIPE,
                      stderr=PIPE)
        data = p.communicate()[0]
        data = data.decode(encoding='UTF-8').split("\n")[1:-1]
        files = []
        self.filesize = {}
        for fil in data:
            fil = fil.split()
            # Catch stupid filenames with whitespaces
            filename = " ".join(fil[8:])
            files.append(filename)
            # Number of images in directory as filesize
            if os.path.isdir(filename):
                try:
                    subfiles = listdir_wrapper(filename, self.show_hidden)
                    # Necessary to keep acceptable speed in library
                    many = False
                    if len(subfiles) > self.file_check_amount:
                        many = True
                    subfiles = [subfile
                                for subfile in subfiles[:self.file_check_amount]
                                if is_image(os.path.join(filename, subfile))]
                    amount = str(len(subfiles))
                    if subfiles and many:
                        amount += "+"
                    self.filesize[filename] = amount
                except:
                    self.filesize[filename] = "N/A"
            else:
                self.filesize[filename] = fil[4]

        return files

    def scroll(self, direction):
        """ Scroll the library viewer and select if necessary """
        # Handle the specific keys
        if direction == "h":  # Behave like ranger
            self.remember_pos(os.getcwd(), self.treepos)
            self.move_up()
        elif direction == "l":
            self.file_select("a", Gtk.TreePath(self.treepos), "b", False)
        else:
            # Scroll the tree checking for a user step
            if self.vimiv.keyhandler.num_str:
                step = int(self.vimiv.keyhandler.num_str)
            else:
                step = 1
            if direction == "j":
                new_pos = self.treepos + step
                if new_pos >= len(self.file_liststore):
                    new_pos = len(self.file_liststore) - 1
            else:
                new_pos = self.treepos - step
                if new_pos < 0:
                    new_pos = 0
            self.move_pos(True, new_pos)
        return True  # Deactivates default bindings (here for Arrows)
