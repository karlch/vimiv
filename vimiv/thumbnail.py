#!/usr/bin/env python
# encoding: utf-8
""" Thumbnail part of vimiv """

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from vimiv.imageactions import thumbnails_create


class Thumbnail(object):
    """ Thumbnail class for vimiv
        includes the iconview with the thumnbails and all actions that apply to
        it """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Settings
        self.toggled = False
        self.size = general["thumbsize"]
        self.cache = general["cache_thumbnails"]
        self.directory = os.path.join(self.vimiv.directory, "Thumbnails")
        self.timer_id = GLib.Timeout
        self.errorpos = 0
        self.pos = 0
        self.elements = []

        # Creates the Gtk elements necessary for thumbnail mode, fills them
        # and focuses the iconview
        # Create the liststore and iconview
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconview = Gtk.IconView.new()
        self.iconview.connect("item-activated", self.iconview_clicked)
        self.iconview.connect("key_press_event", self.vimiv.keyhandler.run,
                              "THUMBNAIL")
        self.iconview.set_model(self.liststore)
        self.columns = 0
        self.iconview.set_spacing(0)
        self.iconview.set_item_width(5)
        self.iconview.set_item_padding(10)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_border_width(1)
        self.iconview.set_markup_column(1)

    def iconview_clicked(self, w, count):
        """ Selects image when thumbnail was selected """
        # Move to the current position if the iconview is clicked
        self.toggle()
        count = count.get_indices()[0] + 1
        self.vimiv.keyhandler.vimiv.keyhandler.num_clear()
        for i in self.errorpos:
            if count > i:
                count += 1
        self.vimiv.keyhandler.vimiv.keyhandler.num_str = str(count)
        self.vimiv.image.move_pos()

    def toggle(self):
        """ Toggles thumbnail mode """
        if self.toggled:
            self.vimiv.image.scrolled_win.remove(self.iconview)
            self.vimiv.image.scrolled_win.add(self.vimiv.image.viewport)
            self.vimiv.image.update()
            self.vimiv.image.scrolled_win.grab_focus()
            self.toggled = False
        elif self.vimiv.paths:
            self.show()
            # Scroll to thumb
            self.timer_id = GLib.timeout_add(1, self.move_to_pos, self.pos)
            # Let the library keep focus
            if self.vimiv.library.treeview.is_focus():
                self.vimiv.library.treeview.grab_focus()
            # Manipulate bar is useless in thumbnail mode
            if self.vimiv.manipulate.toggled:
                self.vimiv.manipulate.toggle()
        else:
            self.vimiv.statusbar.vimiv.statusbar.err_message("No open image")
        # Update info for the current mode
        if not self.errorpos:
            self.vimiv.statusbar.update_info()

    def calculate_columns(self):
        """ Calculates how many columns fit into the current window and sets
            them for the iconview """
        window_width = self.vimiv.winsize[0]
        if self.vimiv.library.toggled:
            width = window_width - self.vimiv.library.width
        else:
            width = window_width
        self.columns = int(width / (self.size[0] + 30))
        self.iconview.set_columns(self.columns)

    def show(self):
        """ Shows thumbnail mode when called from toggle """
        # Clean liststore
        self.liststore.clear()
        # Create thumbnails
        self.elements, errtuple = thumbnails_create(self.vimiv.paths, self.size)
        self.errorpos = errtuple[0]
        if self.errorpos:
            failed_files = ", ".join(errtuple[1])
            self.vimiv.statusbar.err_message(
                "Thumbnail creation for %s failed" % (failed_files))

        # Add all thumbnails to the liststore
        for i, thumb in enumerate(self.elements):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumb)
            name = os.path.basename(thumb)
            name = name.split(".")[0]
            if self.vimiv.paths[i] in self.vimiv.mark.marked:
                name = name + " [*]"
            self.liststore.append([pixbuf, name])

        # Set columns
        self.calculate_columns()

        # Draw the icon view instead of the image
        self.vimiv.image.scrolled_win.remove(self.vimiv.image.viewport)
        self.vimiv.image.scrolled_win.add(self.iconview)

        # Show the window
        self.iconview.show()
        self.toggled = True

        # Focus the current immage
        self.iconview.grab_focus()
        pos = (self.vimiv.index) % len(self.vimiv.paths)
        for i in self.errorpos:
            if pos > i:
                pos -= 1
        self.move_to_pos(pos)

        # Remove the files again if the thumbnails should not be cached
        if not self.cache:
            for thumb in self.elements:
                os.remove(thumb)

    def reload(self, thumb, index, reload_image=True):
        """ Reloads the thumbnail of manipulated images """
        for i in self.errorpos:
            if index > i:
                index -= 1
        liststore_iter = self.liststore.get_iter(index)
        self.liststore.remove(liststore_iter)
        try:
            if reload_image:
                new_thumb = thumbnails_create([thumb], self.size)[0]
                self.elements[index] = new_thumb[0]
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.elements[index])

            name = os.path.basename(self.elements[index])
            name = name.split(".")[0]

            if thumb in self.vimiv.mark.marked:
                name = name + " [*]"
            self.liststore.insert(index, [pixbuf, name])
            path = Gtk.TreePath.new_from_string(str(self.pos))
            self.iconview.select_path(path)
            curthing = self.iconview.get_cells()[0]
            self.iconview.set_cursor(path, curthing, False)
        except:
            message = "Reload of manipulated thumbnails failed"
            self.vimiv.statusbar.err_message(message)

    def move_direction(self, direction):
        """ Find out correct position to move to when scrolling with hjkl and
            call move_to_pos with the position """
        pos = self.pos
        # Get last element
        last = len(self.vimiv.paths) - len(self.errorpos) - 1
        # Check for a user prefixed step
        if self.vimiv.keyhandler.num_str:
            step = int(self.vimiv.keyhandler.num_str)
        else:
            step = 1
        # Check for the specified thumbnail and handle exceptons
        if direction == "h":
            pos -= step
        elif direction == "k":
            pos -= self.columns * step
        elif direction == "l":
            pos += step
        elif direction == "j":
            pos += self.columns * step
        # Allow numbers to be passed directly
        else:
            pos = direction
        # Do not scroll to self.vimiv.paths that don't exist
        if pos < 0:
            pos = 0
        elif pos > last:
            pos = last
        # Move
        self.move_to_pos(pos)

    def move_to_pos(self, pos):
        """ Focus the thumbnail at pos and center it in iconview """
        self.pos = pos
        self.iconview.select_path(Gtk.TreePath(self.pos))
        current_thumb = self.iconview.get_cells()[0]
        self.iconview.set_cursor(Gtk.TreePath(self.pos), current_thumb, False)
        self.iconview.scroll_to_path(Gtk.TreePath(self.pos), True, 0.5, 0.5)
        # Clear the user prefixed step
        self.vimiv.keyhandler.num_clear()
