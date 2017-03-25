# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Thumbnail part of vimiv."""

import os
from math import floor

from gi.repository import GdkPixbuf, GLib, Gtk
from vimiv.fileactions import populate
from vimiv.thumbnail_manager import ThumbnailManager


class Thumbnail(object):
    """Thumbnail class for vimiv.

    Includes the iconview with the thumnbails and all actions that apply to it.

    Attributes:
        app: The main vimiv application to interact with.
        toggled: If True thumbnail mode is open.
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
        last_focused: Widget that was focused before thumbnail.
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
        self.padding = general["thumb_padding"]
        self.current_size = 0
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
        self.iconview.connect("key_press_event", self.app["eventhandler"].run,
                              "THUMBNAIL")
        self.iconview.connect("button_press_event",
                              self.app["eventhandler"].run, "THUMBNAIL")
        self.iconview.set_model(self.liststore)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_markup_column(1)

        self.columns = 0
        self.iconview.set_item_width(0)
        self.iconview.set_item_padding(self.padding)
        self.last_focused = ""
        self.thumbnail_manager = ThumbnailManager()

    def iconview_clicked(self, iconview, path):
        """Select and show image when thumbnail was activated.

        Args:
            iconview: Gtk.IconView that emitted the signal.
            path: Gtk.TreePath of the activated thumbnail.
        """
        self.toggle(True)
        count = path.get_indices()[0] + 1
        self.app["eventhandler"].num_clear()
        self.app["eventhandler"].num_str = str(count)
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
            if self.last_focused == "im" or select_image:
                self.app["image"].scrolled_win.grab_focus()
            elif self.last_focused == "lib":
                self.app["library"].focus()
                # Re-expand the library if there is no image and the setting
                # applies
                if self.app["library"].expand and \
                                self.app["image"].pixbuf_original.get_height() == 1:
                    self.app["image"].scrolled_win.hide()
                    self.app["library"].scrollable_treeview.set_hexpand(True)
            self.toggled = False
        # Open thumbnail mode differently depending on where we come from
        elif self.app.paths and self.app["image"].scrolled_win.is_focus():
            self.last_focused = "im"
            self.show()
        elif self.app["library"].files \
                and self.app["library"].treeview.is_focus():
            self.last_focused = "lib"
            self.app.paths, self.app.index = populate(self.app["library"].files)
            if self.app.paths:
                self.app["library"].scrollable_treeview.set_hexpand(False)
                self.app["image"].scrolled_win.show()
                self.show()
            else:
                self.app["statusbar"].message("No images in directory", "error")
                return
        else:
            self.app["statusbar"].message("No open image", "error")
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
        self.columns = floor((width - 12) / (self.size[0] + 2 * self.padding))
        if self.columns < 1:
            self.columns = 1
        free_space = (width - 12) % (self.size[0] + 2 * self.padding)
        padding = floor(free_space / (self.columns))
        self.iconview.set_column_spacing(padding)
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
        # Draw the icon view instead of the image
        if not toggled:
            self.app["image"].scrolled_win.remove(self.app["image"].viewport)
            self.app["image"].scrolled_win.add(self.iconview)
        # Show the window
        self.iconview.show()
        self.toggled = True

        # Add initial placeholder for all thumbnails
        default_pixbuf_max = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.thumbnail_manager.default_icon, *self.size, True)
        default_pixbuf = self.scale_thumb(default_pixbuf_max)
        for path in self.app.paths:
            self.pixbuf_max.append(default_pixbuf_max)
            name = self._get_name(path)
            self.liststore.append([default_pixbuf, name])

        # Generate thumbnails asynchronously
        for i, path in enumerate(self.app.paths):
            self.thumbnail_manager.get_thumbnail_pixbuf_async(path, i, self._on_thumbnail_created)

        # Set columns
        self.calculate_columns()

        # Focus the current image
        self.iconview.grab_focus()
        pos = self.app.index % len(self.app.paths)
        self.move_to_pos(pos)

    def _on_thumbnail_created(self, position, pixbuf):
        self.pixbuf_max[position] = pixbuf
        scaled = self.scale_thumb(pixbuf)
        self.liststore[position][0] = scaled
        self.calculate_columns()

    def _get_name(self, filename):
        name = os.path.splitext(os.path.basename(filename))[0]
        if filename in self.app["mark"].marked:
            name += " [*]"

        return name

    def reload(self, filename, reload_image=True):
        """Reload the thumbnails of manipulated images.

        Args:
            filename: Name of the file to reload thumbnail of.
            reload_image: If True reload the image of the thumbnail. Else only
                the name (useful for marking).
        """
        index = self.app.paths.index(filename)
        name = self._get_name(filename)
        if index in self.app["commandline"].search_positions:
            name = self.markup + "<b>" + name + "</b></span>"
        # Subsctipting the liststore directly works fine
        # pylint: disable=unsubscriptable-object
        # pylint: disable=unsupported-assignment-operation
        if reload_image:
            self.thumbnail_manager.get_thumbnail_pixbuf_async(filename, index, self._on_thumbnail_created)
        else:
            self.liststore[index][1] = name

    def move_direction(self, direction):
        """Scroll with "hjkl".

        Args:
            direction: Direction to scroll in. One of "hjkl".
        """
        # Start at current position
        new_pos = self.app.get_pos(force_widget="thu")
        # Check for a user prefixed step
        step = self.app["eventhandler"].num_receive()
        # Get variables used for calculation of limits
        last = len(self.app.paths)
        rows = self.iconview.get_item_row(Gtk.TreePath(last - 1))
        elem_last_row = last - rows * self.columns
        elem_per_row = floor((last - elem_last_row) / rows) if rows else last
        column = self.iconview.get_item_column(Gtk.TreePath(new_pos))
        row = self.iconview.get_item_row(Gtk.TreePath(new_pos))
        min_pos = 0
        max_pos = last - 1
        # Simple scrolls
        if direction == "h":
            new_pos -= step
        elif direction == "k":
            min_pos = column
            new_pos -= self.columns * step
        elif direction == "l":
            new_pos += step
        elif direction == "j":
            max_pos = (rows - 1) * elem_per_row + column \
                if column >= elem_last_row else rows * elem_per_row + column
            new_pos += self.columns * step
        # First element in row
        elif direction == "H":
            new_pos = row * elem_per_row
        # Last element in column
        elif direction == "J":
            new_pos = (rows - 1) * elem_per_row + column \
                if column >= elem_last_row else rows * elem_per_row + column
        # First element in column
        elif direction == "K":
            new_pos %= elem_per_row
        # Last element in row
        elif direction == "L":
            new_pos = (row + 1) * elem_per_row - 1
        # Do not scroll to paths that are over the limits
        if new_pos < min_pos:
            new_pos = min_pos
        elif new_pos > max_pos:
            new_pos = max_pos
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
        self.app["eventhandler"].num_clear()

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
                # Subsctipting the liststore directly works fine
                # pylint: disable=unsubscriptable-object
                pixbuf_max = self.pixbuf_max[i]
                pixbuf = self.scale_thumb(pixbuf_max)
                self.liststore[i][0] = pixbuf

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
