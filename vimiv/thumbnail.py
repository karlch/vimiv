# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Thumbnail part of vimiv."""

import os
from math import floor

from gi.repository import GdkPixbuf, GLib, Gtk
from vimiv.fileactions import populate
from vimiv.thumbnail_manager import ThumbnailManager


class Thumbnail(Gtk.IconView):
    """Thumbnail class for vimiv.

    Includes the iconview with the thumnbails and all actions that apply to it.

    Attributes:
        app: The main vimiv application to interact with.
        toggled: If True thumbnail mode is open.
        zoom_levels: List of tuples containing the possible thumbnail sizes.
        zoom_level_index: Position in the possible_sizes list.
        timer_id: ID of the currently running GLib.Timeout.
            creation failed.
        elements: List containing names of current thumbnail-files.
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
        super(Thumbnail, self).__init__()
        self.app = app
        general = settings["GENERAL"]

        # Settings
        self.toggled = False
        self.padding = general["thumb_padding"]
        self.timer_id = GLib.Timeout
        self.elements = []
        self.markup = settings["LIBRARY"]["markup"].replace("fore", "back")

        zoom_level = general["default_thumbsize"]
        self.zoom_levels = [(64, 64), (128, 128), (256, 256), (512, 512)]
        self.zoom_level_index = self.zoom_levels.index(zoom_level)

        # Creates the Gtk elements necessary for thumbnail mode, fills them
        # and focuses the iconview
        # Create the liststore and iconview
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.connect("item-activated", self.clicked)
        self.connect("key_press_event",
                     self.app["eventhandler"].key_pressed, "THUMBNAIL")
        self.connect("button_press_event",
                     self.app["eventhandler"].clicked, "THUMBNAIL")
        self.set_model(self.liststore)
        self.set_pixbuf_column(0)
        self.set_markup_column(1)

        self.columns = 0
        self.set_item_width(0)
        self.set_item_padding(self.padding)
        self.last_focused = ""
        self.thumbnail_manager = ThumbnailManager()

        # Connect signals
        self.app.connect("widgets_changed", self._on_widgets_changed)

    def clicked(self, iconview, path):
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
            self.app["main_window"].switch_to_child(self.app["image"])
            if self.last_focused == "im" or select_image:
                self.app["main_window"].grab_focus()
            elif self.last_focused == "lib":
                self.app["library"].focus()
                # Re-expand the library if there is no image and the setting
                # applies
                if self.app["library"].expand and \
                        self.app["image"].pixbuf_original.get_height() == 1:
                    self.app["main_window"].hide()
                    self.app["library"].scrollable_treeview.set_hexpand(True)
            self.toggled = False
        # Open thumbnail mode differently depending on where we come from
        elif self.app.paths and self.app["main_window"].is_focus():
            self.last_focused = "im"
            self.show()
        elif self.app["library"].files \
                and self.app["library"].is_focus():
            self.last_focused = "lib"
            self.app.paths, self.app.index = populate(self.app["library"].files)
            if self.app.paths:
                self.app["library"].scrollable_treeview.set_hexpand(False)
                self.app["main_window"].show()
                self.show()
            else:
                self.app["statusbar"].message("No images in directory", "error")
                return
        else:
            self.app["statusbar"].message("No open image", "error")
            return
        # Manipulate bar is useless in thumbnail mode
        if self.app["manipulate"].is_visible():
            self.app["manipulate"].toggle()
        self.app.emit("widgets-changed", self)

    def calculate_columns(self):
        """Calculate how many columns fit into the current window."""
        width = self.app["window"].winsize[0]
        if self.app["library"].grid.is_visible():
            width -= self.app["library"].width

        self.columns = floor(
            (width - 12) / (self.get_zoom_level()[0] + 2 * self.padding))
        if self.columns < 1:
            self.columns = 1
        free_space = (width - 12) % (
            self.get_zoom_level()[0] + 2 * self.padding)
        padding = floor(free_space / self.columns)
        self.set_column_spacing(padding)
        self.set_columns(self.columns)

    def show(self, toggled=False):
        """Show thumbnails when called from toggle.

        Args:
            toggled: If True thumbnail mode is already toggled.
        """
        # Clean liststore
        self.liststore.clear()

        # Draw the icon view instead of the image
        if not toggled:
            self.app["main_window"].switch_to_child(self)
        # Show the window
        super(Thumbnail, self).show()
        self.toggled = True

        # Add initial placeholder for all thumbnails
        default_pixbuf_max = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            self.thumbnail_manager.default_icon,
            *self.get_zoom_level(), True)
        size = self.get_zoom_level()[0]
        default_pixbuf = self.thumbnail_manager.scale_pixbuf(default_pixbuf_max,
                                                             size)
        for path in self.app.paths:
            name = self._get_name(path)
            self.liststore.append([default_pixbuf, name])

        # Generate thumbnails asynchronously
        self.reload_all(ignore_cache=True)

        # Set columns
        self.calculate_columns()

        # Focus the current image
        self.grab_focus()
        pos = self.app.index % len(self.app.paths)
        self.move_to_pos(pos)

    def reload_all(self, ignore_cache=False):
        size = self.get_zoom_level()[0]
        for i, path in enumerate(self.app.paths):
            self.thumbnail_manager.get_thumbnail_at_scale_async(
                path, size, self._on_thumbnail_created, i,
                ignore_cache=ignore_cache)

    def _on_thumbnail_created(self, pixbuf, position):
        # Subsctipting the liststore directly works fine
        # pylint: disable=unsubscriptable-object
        self.liststore[position][0] = pixbuf
        self.move_to_pos(self.app.get_pos(force_widget="thu"))

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

        # pylint: disable=unsubscriptable-object
        if reload_image:
            self.thumbnail_manager.get_thumbnail_at_scale_async(
                filename, self.get_zoom_level()[0],
                self._on_thumbnail_created, index, ignore_cache=True)

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
        rows = self.get_item_row(Gtk.TreePath(last - 1))
        elem_last_row = last - rows * self.columns
        elem_per_row = floor((last - elem_last_row) / rows) if rows else last
        column = self.get_item_column(Gtk.TreePath(new_pos))
        row = self.get_item_row(Gtk.TreePath(new_pos))
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
        self.select_path(Gtk.TreePath(pos))
        cell_renderer = self.get_cells()[0]
        self.set_cursor(Gtk.TreePath(pos), cell_renderer, False)
        self.scroll_to_path(Gtk.TreePath(pos), True, 0.5, 0.5)
        # Clear the user prefixed step
        self.app["eventhandler"].num_clear()

    def zoom(self, inc=True):
        """Zoom thumbnails.

        Args:
            inc: If True increase thumbnail size.
        """
        # What zoom and limits
        if inc and self.zoom_level_index < len(self.zoom_levels) - 1:
            self.zoom_level_index += 1
        elif not inc and self.zoom_level_index > 0:
            self.zoom_level_index -= 1
        else:
            return

        # Rescale all images in liststore
        if self.toggled:
            self.reload_all()

        # Set columns and refocus current image
        self.calculate_columns()
        self.move_to_pos(self.app.get_pos(force_widget="thu"))

    def get_zoom_level(self):
        return self.zoom_levels[self.zoom_level_index]

    def _on_widgets_changed(self, app, widget):
        """Recalculate thumbnails if necessary when the layout changed.

        Args:
            app: Vimiv application that emitted the signal.
            widget: Widget that has changed.
        """
        if self.toggled:
            self.calculate_columns()
