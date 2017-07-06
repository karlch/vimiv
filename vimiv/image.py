# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Image part of vimiv."""

from random import shuffle
from threading import Thread

from gi.repository import GdkPixbuf, GLib, Gtk
from vimiv.helpers import get_float_from_str
from vimiv.fileactions import is_animation


class Image(Gtk.Image):
    """Image class for vimiv.

    Inherits from Gtk.Image and includes all actions that apply to it.

    Attributes:
        fit_image:
            user: Image is user zoomed.
            overzoom: Image is zoomed to fit respecting overzoom.
            horizontal: Image is zoomed to fit horizontally.
            vertical: Image is zoomed to fit vertically.
            fit: Image is zoomed to fit.
        pixbuf_iter: Iter of displayed animation.
        pixbuf_original: Original image.
        zoom_percent: Percentage to zoom to compared to the original size.

        _animation_toggled: If True, animation is playing.
        _app: The main vimiv class to interact with.
        _autoplay_gifs: If True, autoplay animations.
        _identifier: Used so GUI callbacks are only done if the image is equal
        _overzoom: Float describing the maximum amount to zoom images above
            their default size.
        _rescale_svg: If True rescale vector graphics when zooming.
        _shuffle: If True randomly shuffle paths.
        _size: Size of the displayed image as a tuple.
        _timer_id: Id of current animation timer.
    """

    def __init__(self, app, settings):
        """Set default values for attributes."""
        super(Image, self).__init__()
        self._app = app
        general = settings["GENERAL"]

        # Settings and defaults
        self.fit_image = "overzoom"
        self.pixbuf_iter = GdkPixbuf.PixbufAnimationIter()
        self.pixbuf_original = GdkPixbuf.Pixbuf()
        self.zoom_percent = 1
        self._animation_toggled = False
        self._autoplay_gifs = general["autoplay_gifs"]
        self._identifier = 0
        self._overzoom = general["overzoom"]
        self._rescale_svg = general["rescale_svg"]
        self._shuffle = general["shuffle"]
        self._size = (0, 0)
        self._timer_id = 0

        # Connect signals
        self._app["transform"].connect("changed", self._on_image_changed)
        self._app["commandline"].search.connect("search-completed",
                                                self._on_search_completed)

    def update(self, update_info=True):
        """Show the final image.

        Args:
            update_info: If True update the statusbar with new information.
        """
        if not self._app.get_paths():
            return
        # Scale image
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()
        pbf_width = int(pbo_width * self.zoom_percent)
        pbf_height = int(pbo_height * self.zoom_percent)
        # Rescaling of svg
        name = self._app.get_path()
        info = GdkPixbuf.Pixbuf.get_file_info(name)[0]
        if info and "svg" in info.get_extensions():
            pixbuf_final = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                name, -1, pbf_height, True)
        else:
            pixbuf_final = self.pixbuf_original.scale_simple(
                pbf_width, pbf_height, GdkPixbuf.InterpType.BILINEAR)
        self.set_from_pixbuf(pixbuf_final)
        # Update the statusbar if required
        if update_info:
            self._app["statusbar"].update_info()

    def zoom_delta(self, zoom_in=True, step=1):
        """Zoom the image by delta percent.

        Args:
            zoom_in: If True zoom in, else zoom out.
        """
        delta = 0.25
        # Allow user steps
        step = self._app["eventhandler"].num_receive(step, True)
        if isinstance(step, str):
            step, err = get_float_from_str(step)
            if err:
                self._app["statusbar"].message(
                    "Argument for zoom must be of type float", "error")
                return
        fallback_zoom = self.zoom_percent
        if zoom_in:
            self.zoom_percent = self.zoom_percent * (1 + delta * step)
        else:
            self.zoom_percent = self.zoom_percent / (1 + delta * step)
        self._catch_unreasonable_zoom_and_update(fallback_zoom)
        self.fit_image = "user"

    def zoom_to(self, percent=0, fit="fit"):
        """Zoom to a given percentage.

        Args:
            percent: Percentage to zoom to.
            fit: How to fit image if percent is not given.
        """
        fallback_zoom = self.zoom_percent
        # Catch user zooms
        percent = self._app["eventhandler"].num_receive(percent, True)
        # Given from commandline
        if isinstance(percent, str):
            percent, err = get_float_from_str(percent)
            if err:
                self._app["statusbar"].message(
                    "Argument for zoom must be of type float", "error")
                return
        self._size = self._get_available_size()
        # 0 means zoom to fit
        if percent:
            self.zoom_percent = percent
            self.fit_image = "user"
        else:
            self.zoom_percent = self.get_zoom_percent_to_fit(fit)
            self.fit_image = fit
        # Catch some unreasonable zooms
        self._catch_unreasonable_zoom_and_update(fallback_zoom)

    def move_index(self, forward=True, key=None, delta=1, force=False):
        """Move by delta in paths.

        Args:
            forward: If True move forwards. Else move backwards.
            key: If available, move by key.
            delta: Positions to move by.
            force: If True, move regardless of editing image.
        """
        # Check if an image is opened or if it has been edited
        if not self._app.get_paths() or self._app["thumbnail"].toggled or \
                self._app["manipulate"].check_for_edit(force):
            return
        # Apply done rotations and flips to file
        self._app["transform"].apply()
        # Check for prepended numbers and direction
        if key:
            delta *= self._app["eventhandler"].num_receive()
        if not forward:
            delta *= -1
        self._app.update_index(delta)
        self.fit_image = "overzoom"

        # Reshuffle on wrap-around
        if self._shuffle and self._app.get_index() is 0 and delta > 0:
            shuffle(self._app.get_paths())

        # Load the image at path into self.pixbuf_* and show it
        self.load()

    def load(self):
        """Load an image using GdkPixbufLoader."""
        path = self._app.get_path()
        # Remove old timers and reset scale
        if self._timer_id:
            self.zoom_percent = 1
            self._pause_gif()
        # Load file
        try:
            self._load(path)
        except (PermissionError, FileNotFoundError):
            self._app.remove_path(path)
            self.move_pos(False)
            self._app["statusbar"].message("File not accessible", "error")

    def move_pos(self, forward=True, force=False):
        """Move to specific position in paths.

        Args:
            forward: If True move forwards. Else move backwards.
            force: If True, move regardless of editing image.
        """
        # Check if image has been edited
        if self._app["manipulate"].check_for_edit(force):
            return
        max_pos = len(self._app.get_paths())
        current = self._app.get_index()
        # Move to definition by keys or end/beg
        if forward:
            pos = self._app["eventhandler"].num_receive(max_pos)
        else:
            pos = self._app["eventhandler"].num_receive()
        # Catch range
        if pos < 0 or pos > max_pos:
            self._app["statusbar"].message("Unsupported index", "warning")
            return
        # Do the maths and move
        if self._app["thumbnail"].toggled:
            self._app["thumbnail"].move_to_pos(pos - 1)
        else:
            self.move_index(True, False, pos - current - 1)

    def toggle_rescale_svg(self):
        """Toggle rescale state of vector images."""
        self._rescale_svg = not self._rescale_svg

    def set_overzoom(self, new_value="1"):
        """Set overzoom of images."""
        new_value, error = get_float_from_str(new_value)
        if error:
            self._app["statusbar"].message(
                "Argument for zoom must be of type float", "error")
            return
        self._overzoom = new_value
        # Update image if it makes sense
        if self.fit_image != "user":
            self.zoom_percent = self.get_zoom_percent_to_fit(self.fit_image)
            self.update()

    def toggle_animation(self):
        """Toggle animation status of Gifs."""
        if self._app.get_paths() and is_animation(self._app.get_path()) \
                and not self._app["thumbnail"].toggled:
            if self._animation_toggled:
                self._pause_gif()
            else:
                self._play_gif()

    def get_scroll_scale(self):
        return self.zoom_percent / self.get_zoom_percent_to_fit() * 2

    def get_zoom_percent(self):
        return self.zoom_percent * 100

    def get_zoom_percent_to_fit(self, fit="fit"):
        """Get the zoom factor perfectly fitting the image to the window.

        Args:
            fit: How to fit image.
        Return:
            Zoom percentage.
        """
        # Size of the file
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()
        # Maximum size respecting overzoom
        max_width = pbo_width * self._overzoom
        max_height = pbo_height * self._overzoom
        # Get scales for "panorama" vs "portrait" image
        w_scale = pbo_width / self._size[0]
        h_scale = pbo_height / self._size[1]
        scale_width = True if w_scale > h_scale else False
        # Check if image fits completely with overzoom
        fits = max_width < self._size[0] and max_height < self._size[1]
        # Image fits completely even with overzoom and we do not want to fit
        if fits and fit in ["user", "overzoom"]:
            return self._overzoom
        # Force horizontal fit or "panorama" image
        elif fit == "horizontal" or (scale_width and fit != "vertical"):
            return self._size[0] / pbo_width
        # Force vertical fit or "portrait" image
        return self._size[1] / pbo_height

    def _catch_unreasonable_zoom_and_update(self, fallback_zoom):
        """Catch unreasonable zooms otherwise update.

        Args:
            fallback_zoom: Zoom percentage to fall back to if the zoom
                percentage is unreasonable.
        """
        orig_width = self.pixbuf_original.get_width()
        orig_height = self.pixbuf_original.get_height()
        new_width = orig_width * self.zoom_percent
        new_height = orig_height * self.zoom_percent
        min_width = max(16, orig_width * 0.05)
        min_height = max(16, orig_height * 0.05)
        max_width = min(self._app["window"].get_size()[0] * 10,
                        self.pixbuf_original.get_width() * 20)
        max_height = min(self._app["window"].get_size()[1] * 10,
                         self.pixbuf_original.get_height() * 20)
        # Image too small or too large
        if new_height < min_height or new_width < min_width \
                or new_height > max_height or new_width > max_width:
            # Warn user if it was his fault
            if self.fit_image == "user":
                message = "Image cannot be zoomed this far"
                self._app["statusbar"].message(message, "warning")
                self.zoom_percent = fallback_zoom
            return
        self.update()

    def _play_gif(self):
        """Run the animation of a gif."""
        self._animation_toggled = True
        self.pixbuf_original = self.pixbuf_iter.get_pixbuf()
        GLib.idle_add(self.update)
        if self.pixbuf_iter.advance():
            # Clear old timer
            if self._timer_id:
                GLib.source_remove(self._timer_id)
            # Add new timer if the gif is not static
            delay = self.pixbuf_iter.get_delay_time()
            self._timer_id = GLib.timeout_add(delay, self._play_gif) \
                if delay >= 0 else 0

    def _pause_gif(self):
        """Pause a gif or show initial image."""
        self._animation_toggled = False
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0
        else:
            image = self.pixbuf_iter.get_pixbuf()
            self.set_from_pixbuf(image)

    def _get_available_size(self):
        """Receive size not occupied by other Widgets.

        Subtracts other widgets (manipulate, statusbar, library) from window
        size and returns the available size.

        Return:
            Tuple of available size.
        """
        size = self._app["window"].get_size()
        if self._app["library"].grid.is_visible():
            library_width = self._app["library"].get_size_request()[0]
            size = (size[0] - library_width, size[1])
        if not self._app["statusbar"].hidden:
            size = (size[0], size[1] - self._app["statusbar"].get_bar_height())
        return size

    def _load(self, path):
        """Actual implementation to load an image from path."""
        loader = GdkPixbuf.PixbufLoader()
        self._identifier += 1
        if is_animation(path):
            loader.connect("area-prepared", self._set_image_anim)
        else:
            loader.connect("area-prepared", self._set_image_pixbuf)
            loader.connect("closed",
                           self._finish_image_pixbuf, self._identifier)
        load_thread = Thread(target=self._load_thread, args=(loader, path),
                             daemon=True)
        # Daemon is set to True so the program can exit with "q" immediately if
        # only a loading thread is left
        load_thread.start()

    def _load_thread(self, loader, path):
        with open(path, "rb") as f:
            loader.write(f.read())
        loader.close()

    def _set_image_pixbuf(self, loader):
        self.pixbuf_original = loader.get_pixbuf()
        self._size = self._get_available_size()
        self.zoom_percent = self.get_zoom_percent_to_fit(self.fit_image)

    def _finish_image_pixbuf(self, loader, image_id):
        if self._identifier == image_id:
            GLib.idle_add(self.update)

    def _set_image_anim(self, loader):
        self.pixbuf_iter = loader.get_animation().get_iter()
        self.pixbuf_original = self.pixbuf_iter.get_pixbuf()
        self._size = self._get_available_size()
        self.zoom_percent = self.get_zoom_percent_to_fit(self.fit_image)
        if self._autoplay_gifs:
            delay = self.pixbuf_iter.get_delay_time()
            self._timer_id = GLib.timeout_add(delay, self._play_gif) \
                if delay >= 0 else 0

    # Needed for test suite
    def get_rescale_svg(self):
        return self._rescale_svg

    def get_overzoom(self):
        return self._overzoom

    def get_animation_toggled(self):
        return self._animation_toggled

    def _on_image_changed(self, transform, change, arg):
        """Update image after a transformation.

        Args:
            transform: The transform object that emitted the signal.
            change: The type of transformation.
            arg: Argument for the transformation, e.g. cwise for rotate.
        """
        if change == "rotate":
            self.pixbuf_original = self.pixbuf_original.rotate_simple(90 * arg)
        elif change == "flip":
            self.pixbuf_original = self.pixbuf_original.flip(arg)
        if self.fit_image != "user":
            self.zoom_to(0, self.fit_image)
        else:
            self.update()

    def _on_search_completed(self, search, new_pos, last_focused):
        if last_focused == "im":
            self._app["eventhandler"].num_str = str(new_pos + 1)
            self.move_pos()
