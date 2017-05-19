# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Thumbnail part of vimiv."""

import os
from math import floor

from gi.repository import GdkPixbuf, GLib, Gtk
from vimiv.thumbnail_manager import ThumbnailManager


class Thumbnail(Gtk.IconView):
    """Thumbnail class for vimiv.

    Includes the iconview with the thumnbails and all actions that apply to it.

    Attributes:
        toggled: If True, thumbnail mode is open.

        _app: The main vimiv application to interact with.
        _last_focused: Widget that was focused before thumbnail.
        _liststore: Gtk.ListStore containing thumbnail pixbufs and names.
        _markup: Markup string used to highlight search results.
        _thumbnail_manager: ThumbnailManager class to create and receive
            thumbnail files.
        _timer_id: ID of the currently running GLib.Timeout.
        _zoom_levels: List of tuples containing the possible thumbnail sizes.
        _zoom_level_index: Position in the possible_sizes list.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main application class to interact with.
            settings: Settings from configfiles to use.
        """
        super(Thumbnail, self).__init__()
        self._app = app
        general = settings["GENERAL"]

        # Settings
        self.toggled = False
        padding = general["thumb_padding"]
        self._timer_id = GLib.Timeout
        self._markup = settings["LIBRARY"]["markup"].replace("fore", "back")

        zoom_level = general["default_thumbsize"]
        self._zoom_levels = [(64, 64), (128, 128), (256, 256), (512, 512)]
        self._zoom_level_index = self._zoom_levels.index(zoom_level)

        # Create the liststore and iconview
        self._liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.connect("item-activated", self._on_activated)
        self.connect("key_press_event",
                     self._app["eventhandler"].on_key_press, "THUMBNAIL")
        self.connect("button_press_event",
                     self._app["eventhandler"].on_click, "THUMBNAIL")
        self.set_model(self._liststore)
        self.set_pixbuf_column(0)
        self.set_markup_column(1)

        self.set_item_width(0)
        self.set_item_padding(padding)
        self.last_focused = ""
        self._thumbnail_manager = ThumbnailManager()

        # Signals
        self._app["mark"].connect("marks-changed", self._on_marks_changed)
        self._app["transform"].connect("applied-to-file",
                                       self._on_transformations_applied_to_file)

    def _on_activated(self, iconview, path):
        """Select and show image when thumbnail was activated.

        Args:
            iconview: Gtk.IconView that emitted the signal.
            path: Gtk.TreePath of the activated thumbnail.
        """
        self.toggle(True)
        count = path.get_indices()[0] + 1
        self._app["eventhandler"].num_clear()
        self._app["eventhandler"].num_str = str(count)
        self._app["image"].move_pos()

    def toggle(self, select_image=False):
        """Toggle thumbnail mode.

        Args:
            select_image: If True an image was selected. Never focus the library
                then.
        """
        # Close
        if self.toggled:
            self._app["main_window"].switch_to_child(self._app["image"])
            if self.last_focused == "im" or select_image:
                self._app["main_window"].grab_focus()
            elif self.last_focused == "lib":
                self._app["library"].focus()
                # Re-expand the library if there is no image and the setting
                # applies
                if self._app["library"].expand and \
                        self._app["image"].pixbuf_original.get_height() == 1:
                    self._app["main_window"].hide()
                    self._app["library"].set_hexpand(True)
            self.toggled = False
        # Open thumbnail mode differently depending on where we come from
        elif self._app.get_paths() and self._app.get_focused_widget() == "im":
            self.last_focused = "im"
            self._show()
        elif self._app.get_focused_widget() == "lib":
            self.last_focused = "lib"
            self._app.populate(self._app["library"].files)
            if self._app.get_paths():
                self._app["library"].set_hexpand(False)
                self._app["main_window"].show()
                self._show()
            else:
                self._app["statusbar"].message(
                    "No images in directory", "error")
                return
        else:
            self._app["statusbar"].message("No open image", "error")
            return
        # Manipulate bar is useless in thumbnail mode
        if self._app["manipulate"].is_visible():
            self._app["manipulate"].toggle()
        self._app.emit("widgets-changed", self)

    def _show(self, toggled=False):
        """Show thumbnails when called from toggle.

        Args:
            toggled: If True thumbnail mode is already toggled.
        """
        # Clean liststore
        self._liststore.clear()

        # Draw the icon view instead of the image
        if not toggled:
            self._app["main_window"].switch_to_child(self)
        # Show the window
        super(Thumbnail, self).show()
        self.toggled = True

        # Add initial placeholder for all thumbnails
        default_pixbuf = self._get_default_pixbuf()
        for path in self._app.get_paths():
            name = self._get_name(path)
            self._liststore.append([default_pixbuf, name])

        # Generate thumbnails asynchronously
        self.reload_all(ignore_cache=True)

        # Set columns
        self.calculate_columns()

        # Focus the current image
        self.grab_focus()
        pos = self._app.get_index()
        self.move_to_pos(pos)

    def calculate_columns(self):
        """Calculate how many columns fit into the current window."""
        width = self._app["window"].winsize[0]
        if self._app["library"].grid.is_visible():
            width -= self._app["library"].get_size_request()[0]

        padding = self.get_item_padding()
        columns = floor((width - 12) / (self.get_zoom_level()[0] + 2 * padding))
        columns = max(1, columns)  # We may receive zero before
        free_space = (width - 12) % (
            self.get_zoom_level()[0] + 2 * padding)
        padding = floor(free_space / columns)
        self.set_column_spacing(padding)
        self.set_columns(columns)

    def _get_default_pixbuf(self):
        default_pixbuf_max = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            self._thumbnail_manager.default_icon, *self.get_zoom_level(), True)
        size = self.get_zoom_level()[0]
        return self._thumbnail_manager.scale_pixbuf(default_pixbuf_max, size)

    def reload_all(self, ignore_cache=False):
        size = self.get_zoom_level()[0]
        for i, path in enumerate(self._app.get_paths()):
            self._thumbnail_manager.get_thumbnail_at_scale_async(
                path, size, self._on_thumbnail_created, i,
                ignore_cache=ignore_cache)

    def _on_thumbnail_created(self, pixbuf, position):
        # Subsctipting the liststore directly works fine
        # pylint: disable=unsubscriptable-object
        self._liststore[position][0] = pixbuf
        self.move_to_pos(self.get_position())

    def _get_name(self, filename):
        name = os.path.splitext(os.path.basename(filename))[0]
        if filename in self._app["mark"].marked:
            name += " [*]"

        return name

    def reload(self, filename, reload_image=True):
        """Reload the thumbnails of manipulated images.

        Args:
            filename: Name of the file to reload thumbnail of.
            reload_image: If True reload the image of the thumbnail. Else only
                the name (useful for marking).
        """
        index = self._app.get_paths().index(filename)
        name = self._get_name(filename)
        if index in self._app["commandline"].search_positions:
            name = self._markup + "<b>" + name + "</b></span>"

        # pylint: disable=unsubscriptable-object
        if reload_image:
            self._thumbnail_manager.get_thumbnail_at_scale_async(
                filename, self.get_zoom_level()[0],
                self._on_thumbnail_created, index, ignore_cache=True)

        self._liststore[index][1] = name

    def move_direction(self, direction):
        """Scroll with "hjkl".

        Args:
            direction: Direction to scroll in. One of "hjkl".
        """
        # Start at current position
        new_pos = self.get_position()
        # Check for a user prefixed step
        step = self._app["eventhandler"].num_receive()
        # Get variables used for calculation of limits
        last = len(self._app.get_paths())
        rows = self.get_item_row(Gtk.TreePath(last - 1))
        columns = self.get_columns()
        elem_last_row = last - rows * columns
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
            new_pos -= columns * step
        elif direction == "l":
            new_pos += step
        elif direction == "j":
            max_pos = (rows - 1) * elem_per_row + column \
                if column >= elem_last_row else rows * elem_per_row + column
            new_pos += columns * step
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
        self._app["eventhandler"].num_clear()

    def zoom(self, inc=True):
        """Zoom thumbnails.

        Args:
            inc: If True increase thumbnail size.
        """
        # What zoom and limits
        if inc and self._zoom_level_index < len(self._zoom_levels) - 1:
            self._zoom_level_index += 1
        elif not inc and self._zoom_level_index > 0:
            self._zoom_level_index -= 1
        else:
            return
        # Rescale all images in liststore
        if self.toggled:
            self.reload_all()
        # Set columns and refocus current image
        self.calculate_columns()
        self.move_to_pos(self.get_position())

    def get_zoom_level(self):
        return self._zoom_levels[self._zoom_level_index]

    def get_cache_directory(self):
        return self._thumbnail_manager.thumbnail_store.base_dir

    def get_position(self):
        path = self.get_cursor()[1]
        return path.get_indices()[0] if path else 0

    def on_paths_changed(self):
        """Reload thumbnails properly when paths have changed."""
        diff = len(self._liststore) - len(self._app.get_paths())
        # Delete extra elements
        while diff > 0:
            self._liststore.remove(self._liststore[-1].iter)
            diff -= 1
        # Insert dummy elements to override
        default_pixbuf = self._get_default_pixbuf() if diff < 0 else None
        while diff < 0:
            name = self._get_name(self._app.get_paths()[diff])
            self._liststore.append([default_pixbuf, name])
            diff += 1
        for path in self._app.get_paths():
            self.reload(path)

    def _on_marks_changed(self, mark, changed):
        """Reload names if marks changed."""
        if self.toggled:
            for name in changed:
                self.reload(name, False)
        self._app["statusbar"].update_info()  # Do this once from here

    def _on_transformations_applied_to_file(self, transform, files):
        if self.toggled:
            for name in files:
                self.reload(name)
