#!/usr/bin/env python
# encoding: utf-8
"""Thumbnail part of vimiv."""

import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from vimiv.imageactions import Thumbnails
from vimiv.fileactions import populate


class Thumbnail(object):
    """Thumbnail class for vimiv.

    Includes the iconview with the thumnbails and all actions that apply to it.

    Attributes:
        app: The main vimiv application to interact with.
        toggled: If True the library is visible.
        size: Tuple containing the size of thumbnails.
        max_size: Tuple containing the maximum size of thumbnails.
        possible_sizes: List of tuples containing the possible thumbnail sizes.
        current_size: Position in the possible_sizes list.
        cache: If True, cache thumbnails.
        directory: Directory in which thumbnails are stored.
        timer_id: ID of the currently running GLib.Timeout.
            creation failed.
        pos: Current position in the Gtk.IconView.
        elements: List containing names of current thumbnail-files.
        pixbuf_max: List containing current thumbnail-pixbufs at maximum size.
        markup: Markup string used to highlight search results.
        liststore: Gtk.ListStore containing thumbnail pixbufs and names.
        iconview: Gtk.IconView to display thumbnails.
        columns: Amount of columns that fit into the window.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main application class to interact with.
            settings: Settings from configfiles to use.
        """
        self.app = app
        general = settings["GENERAL"]

        # Settings
        self.toggled = False
        self.size = general["thumbsize"]
        self.max_size = general["thumb_maxsize"]
        self.possible_sizes = [(64, 64), (128, 128), (256, 256), (512, 512)]
        self.current_size = 0
        self.cache = general["cache_thumbnails"]
        self.directory = os.path.join(self.app.directory, "Thumbnails")
        self.timer_id = GLib.Timeout
        self.elements = []
        self.pixbuf_max = []
        self.markup = self.app["library"].markup.replace("fore", "back")

        # Prepare thumbnail sizes for zooming of thumbnails
        self.set_sizes()

        # Creates the Gtk elements necessary for thumbnail mode, fills them
        # and focuses the iconview
        # Create the liststore and iconview
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconview = Gtk.IconView.new()
        self.iconview.connect("item-activated", self.iconview_clicked)
        self.iconview.connect("key_press_event", self.app["keyhandler"].run,
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
        self.toggle(True)
        count = path.get_indices()[0] + 1
        self.app["keyhandler"].num_clear()
        self.app["keyhandler"].num_str = str(count)
        self.app["image"].move_pos()

    def toggle(self, select_image=False):
        """Toggle thumbnail mode.

        Args:
            select_image: If True an image was selected. Never focus the library
                then.
        """
        # Close
        if self.toggled:
            self.app["image"].scrolled_win.remove(self.iconview)
            self.app["image"].scrolled_win.add(self.app["image"].viewport)
            if self.app["window"].last_focused == "im" or select_image:
                self.app["image"].scrolled_win.grab_focus()
            elif self.app["window"].last_focused == "lib":
                self.app["library"].focus()
                # Re-expand the library if there is no image and the setting
                # applies
                if self.app["library"].expand:
                    try:
                        self.app["image"].pixbuf_original.get_height()
                    except:
                        self.app["image"].scrolled_win.hide()
                        self.app["library"].scrollable_treeview.set_hexpand(True)
            self.toggled = False
        # Open thumbnail mode differently depending on where we come from
        elif self.app.paths and self.app["image"].scrolled_win.is_focus():
            self.app["window"].last_focused = "im"
            self.show()
        elif self.app["library"].files \
                and self.app["library"].treeview.is_focus():
            self.app["window"].last_focused = "lib"
            self.app.paths, self.app.index = \
                populate(self.app["library"].files)
            self.app["library"].scrollable_treeview.set_hexpand(False)
            if self.app.paths:
                self.app["image"].scrolled_win.show()
            self.show()
        else:
            self.app["statusbar"].err_message("No open image")
            return
        # Manipulate bar is useless in thumbnail mode
        if self.app["manipulate"].scrolled_win.is_visible():
            self.app["manipulate"].toggle()
        # Update info for the current mode
        self.app["statusbar"].update_info()

    def calculate_columns(self):
        """Calculate how many columns fit into the current window."""
        window_width = self.app["window"].winsize[0]
        if self.app["library"].grid.is_visible():
            width = window_width - self.app["library"].width
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
        thumbnails = Thumbnails(self.app.paths, self.sizes[-1])
        self.elements = thumbnails.thumbnails_create()
        # Draw the icon view instead of the image
        if not toggled:
            self.app["image"].scrolled_win.remove(self.app["image"].viewport)
            self.app["image"].scrolled_win.add(self.iconview)
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
            if self.app.paths[i] in self.app["mark"].marked:
                name = name + " [*]"
            self.liststore.append([pixbuf, name])

        # Set columns
        self.calculate_columns()

        # Focus the current image
        self.iconview.grab_focus()
        pos = (self.app.index) % len(self.app.paths)
        self.move_to_pos(pos)

        # Remove the files again if the thumbnails should not be cached
        if not self.cache:
            for thumb in self.elements:
                os.remove(thumb)

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
        liststore_iter = self.liststore.get_iter(index)
        self.liststore.remove(liststore_iter)
        try:
            if reload_image:
                thumbnails = Thumbnails([thumb], self.sizes[-1])
                new_thumb = thumbnails.thumbnails_create()[0]
                self.elements[index] = new_thumb
            pixbuf_max = self.pixbuf_max[index]
            pixbuf = self.scale_thumb(pixbuf_max)

            name = os.path.basename(self.elements[index])
            name = name.split(".")[0]

            if thumb in self.app["mark"].marked:
                name = name + " [*]"
            elif index in self.app["commandline"].search_positions:
                name = self.markup + '<b>' + name + '</b></span>'
            self.liststore.insert(index, [pixbuf, name])
            self.iconview.select_path(old_path)
            cell_renderer = self.iconview.get_cells()[0]
            self.iconview.set_cursor(old_path, cell_renderer, False)
        except:
            message = "Reload of manipulated thumbnails failed"
            self.app["statusbar"].err_message(message)

    def move_direction(self, direction):
        """Scroll with "hjkl".

        Args:
            direction: Direction to scroll in. One of "hjkl".
        """
        new_pos = self.app.get_pos(force_widget="thu")
        # Get last element
        last = len(self.app.paths) - 1
        # Check for a user prefixed step
        if self.app["keyhandler"].num_str:
            step = int(self.app["keyhandler"].num_str)
        else:
            step = 1
        # Check for the specified thumbnail and handle exceptions
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
        # Do not scroll to paths that don't exist
        if new_pos < 0:
            new_pos = 0
        elif new_pos > last:
            new_pos = last
        # Move
        self.move_to_pos(new_pos)

    def move_to_pos(self, pos):
        """Set focus on position in iconview and centre it.

        Args:
            pos: The position to focus.
        """
        self.iconview.select_path(Gtk.TreePath(pos))
        cell_renderer = self.iconview.get_cells()[0]
        self.iconview.set_cursor(Gtk.TreePath(pos), cell_renderer, False)
        self.iconview.scroll_to_path(Gtk.TreePath(pos), True, 0.5, 0.5)
        # Clear the user prefixed step
        self.app["keyhandler"].num_clear()

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
        self.move_to_pos(self.app.get_pos(force_widget="thu"))

    def scale_thumb(self, pixbuf_max):
        """Scale the thumbnail image to self.size.

        Args:
            pixbuf_max: Pixbuf at maximum thumbnail size to scale.

        Return:
            The scaled pixbuf.
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
