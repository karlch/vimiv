#!/usr/bin/env python
# encoding: utf-8
"""Thumbnail part of vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from vimiv.imageactions import Thumbnails


class Thumbnail(object):
    """Thumbnail class for vimiv.

    Includes the iconview with the thumnbails and all actions that apply to it.

    Attributes:
        vimiv: The main vimiv class to interact with.
        toggled: If True the library is visible.
        size: Tuple containing the size of thumbnails.
        max_size: Tuple containing the maximum size of thumbnails.
        possible_sizes: List of tuples containing the possible thumbnail sizes.
        current_size: Position in the possible_sizes list.
        cache: If True, cache thumbnails.
        directory: Directory in which thumbnails are stored.
        timer_id: ID of the currently running GLib.Timeout.
        errorpos: List containing the positions of images where thumbnail
            creation failed.
        pos: Current position in the Gtk.IconView.
        elements: List containing names of current thumbnail-files.
        pixbuf_max: List containing current thumbnail-pixbufs at maximum size.
        listsotre: Gtk.ListStore containing thumbnail pixbufs and names.
        iconview: Gtk.IconView to display thumbnails.
        columns: Amount of columns that fit into the window.
    """

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Settings
        self.toggled = False
        self.size = general["thumbsize"]
        self.max_size = general["thumb_maxsize"]
        self.possible_sizes = [(64, 64), (128, 128), (256, 256), (512, 512)]
        self.current_size = 0
        self.cache = general["cache_thumbnails"]
        self.directory = os.path.join(self.vimiv.directory, "Thumbnails")
        self.timer_id = GLib.Timeout
        self.errorpos = []
        self.elements = []
        self.pixbuf_max = []

        # Prepare thumbnail sizes for zooming of thumbnails
        self.set_sizes()

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

    def iconview_clicked(self, iconview, path):
        """Select and show image when thumbnail was activated.

        Args:
            iconview: Gtk.IconView that emitted the signal.
            path: Gtk.TreePath of the activated thumbnail.
        """
        self.toggle()
        count = path.get_indices()[0] + 1
        self.vimiv.keyhandler.vimiv.keyhandler.num_clear()
        for i in self.errorpos:
            if count > i:
                count += 1
        self.vimiv.keyhandler.vimiv.keyhandler.num_str = str(count)
        self.vimiv.image.move_pos()

    def toggle(self):
        """Toggle thumbnail mode."""
        if self.toggled:
            self.vimiv.image.scrolled_win.remove(self.iconview)
            self.vimiv.image.scrolled_win.add(self.vimiv.image.viewport)
            self.vimiv.image.update()
            self.vimiv.image.scrolled_win.grab_focus()
            self.toggled = False
        elif self.vimiv.paths:
            self.show()
            # Let the library keep focus
            if self.vimiv.library.treeview.is_focus():
                self.vimiv.library.treeview.grab_focus()
            # Manipulate bar is useless in thumbnail mode
            if self.vimiv.manipulate.scrolled_win.is_visible():
                self.vimiv.manipulate.toggle()
        else:
            self.vimiv.statusbar.vimiv.statusbar.err_message("No open image")
        # Update info for the current mode
        if not self.errorpos:
            self.vimiv.statusbar.update_info()

    def calculate_columns(self):
        """Calculate how many columns fit into the current window."""
        window_width = self.vimiv.winsize[0]
        if self.vimiv.library.grid.is_visible():
            width = window_width - self.vimiv.library.width
        else:
            width = window_width
        self.columns = int(width / (self.size[0] + 30))
        self.iconview.set_columns(self.columns)

    def show(self, toggled=False):
        """Show thumbnails when called from toggle.

        Args:
            toggled: If True thumbnail mode is already toggled.
        """
        # Clean liststore
        self.liststore.clear()
        self.pixbuf_max = []
        # Create thumbnails
        thumbnails = Thumbnails(self.vimiv.paths, self.sizes[-1])
        self.elements, errtuple = thumbnails.thumbnails_create()
        self.errorpos = errtuple[0]
        # Draw the icon view instead of the image
        if not toggled:
            self.vimiv.image.scrolled_win.remove(self.vimiv.image.viewport)
            self.vimiv.image.scrolled_win.add(self.iconview)
        # Show the window
        self.iconview.show()
        self.toggled = True

        # Add all thumbnails to the liststore
        for i, thumb in enumerate(self.elements):
            pixbuf_max = GdkPixbuf.Pixbuf.new_from_file(thumb)
            self.pixbuf_max.append(pixbuf_max)
            pixbuf = self.scale_thumb(pixbuf_max)
            name = os.path.basename(thumb)
            name = name.split(".")[0]
            if self.vimiv.paths[i] in self.vimiv.mark.marked:
                name = name + " [*]"
            self.liststore.append([pixbuf, name])

        # Set columns
        self.calculate_columns()

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

        # Show error message if necessary
        if self.errorpos:
            failed_files = ", ".join(
                [os.path.basename(image) for image in errtuple[1]])
            self.vimiv.statusbar.err_message(
                "Thumbnail creation for %s failed" % (failed_files))

    def reload(self, thumb, index, reload_image=True):
        """Reload the thumbnails of manipulated images.

        Args:
            thumb: Thumbnail to reload.
            index: Position of the thumbnail to be reloaded.
            reload_image: If True reload the image of the thumbnail. Else only
                the name (useful for marking).
        """
        # Remember position
        old_path = self.iconview.get_cursor()[1]
        for i in self.errorpos:
            if index > i:
                index -= 1
        liststore_iter = self.liststore.get_iter(index)
        self.liststore.remove(liststore_iter)
        try:
            if reload_image:
                thumbnails = Thumbnails([thumb], self.sizes[-1])
                new_thumb = thumbnails.thumbnails_create()[0]
                self.elements[index] = new_thumb[0]
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.elements[index])

            name = os.path.basename(self.elements[index])
            name = name.split(".")[0]

            if thumb in self.vimiv.mark.marked:
                name = name + " [*]"
            self.liststore.insert(index, [pixbuf, name])
            self.iconview.select_path(old_path)
            cell_renderer = self.iconview.get_cells()[0]
            self.iconview.set_cursor(old_path, cell_renderer, False)
        except:
            message = "Reload of manipulated thumbnails failed"
            self.vimiv.statusbar.err_message(message)

    def move_direction(self, direction):
        """Scroll with "hjkl".

        Args:
            direction: Direction to scroll in. One of "hjkl".
        """
        new_pos = self.vimiv.get_pos()
        # Get last element
        last = len(self.vimiv.paths) - len(self.errorpos) - 1
        # Check for a user prefixed step
        if self.vimiv.keyhandler.num_str:
            step = int(self.vimiv.keyhandler.num_str)
        else:
            step = 1
        # Check for the specified thumbnail and handle exceptons
        if direction == "h":
            new_pos -= step
        elif direction == "k":
            new_pos -= self.columns * step
        elif direction == "l":
            new_pos += step
        elif direction == "j":
            new_pos += self.columns * step
        # Allow numbers to be passed directly
        else:
            new_pos = direction
        # Do not scroll to self.vimiv.paths that don't exist
        if new_pos < 0:
            new_pos = 0
        elif new_pos > last:
            new_pos = last
        # Move
        self.move_to_pos(new_pos)

    def move_to_pos(self, pos):
        """Set focus on position in iconview and center it.

        Args:
            pos: The position to focus.
        """
        self.iconview.select_path(Gtk.TreePath(pos))
        cell_renderer = self.iconview.get_cells()[0]
        self.iconview.set_cursor(Gtk.TreePath(pos), cell_renderer, False)
        self.iconview.scroll_to_path(Gtk.TreePath(pos), True, 0.5, 0.5)
        # Clear the user prefixed step
        self.vimiv.keyhandler.num_clear()

    def zoom(self, inc=True):
        """Zoom thumbnails.

        Args:
            inc: If True increase thumbnail size.
        """
        # What zoom and limits
        if inc and self.current_size < len(self.sizes) - 1:
            self.current_size += 1
        elif not inc and self.current_size > 0:
            self.current_size -= 1
        else:
            return
        self.size = self.sizes[self.current_size]
        # Rescale all images in liststore
        if self.toggled:
            for i in range(len(self.liststore)):
                pixbuf_max = self.pixbuf_max[i]
                pixbuf = self.scale_thumb(pixbuf_max)
                liststore_list = list(self.liststore)
                liststore_list[i][0] = pixbuf

        # Set columns and refocus current image
        self.calculate_columns()
        self.move_to_pos(self.vimiv.get_pos())

    def scale_thumb(self, pixbuf_max):
        """Scale the thumbnail image to self.size.

        Args:
            pixbuf_max: Pixbuf at maximum thumbnail size to scale.

        Return: The scaled pixbuf.
        """
        width = \
            pixbuf_max.get_width() * (float(self.size[0]) / self.max_size[0])
        height = \
            pixbuf_max.get_height() * (float(self.size[1]) / self.max_size[1])
        pixbuf = pixbuf_max.scale_simple(width, height,
                                         GdkPixbuf.InterpType.BILINEAR)
        return pixbuf

    def set_sizes(self):
        """Set maximum size, current size and possible sizes for thumbnails."""
        # Maximum
        if self.max_size[0] >= self.possible_sizes[-1][0]:
            self.sizes = self.possible_sizes
        else:
            for i, size in enumerate(self.possible_sizes):
                if size[0] > self.max_size[0]:
                    self.sizes = self.possible_sizes[0:i]
                    break
        # Current position
        if self.size in self.sizes:
            self.current_size = self.sizes.index(self.size)
        elif self.size[0] > self.sizes[-1][0]:
            self.current_size = len(self.sizes) - 1
            self.size = self.sizes[-1]
        else:
            for i, size in enumerate(self.sizes):
                if size[0] > self.size[0]:
                    self.sizes.insert(i, self.size)
                    self.current_size = i
                    break
