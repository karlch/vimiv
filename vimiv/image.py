# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Image part of vimiv."""

from random import shuffle
from threading import Thread

from gi.repository import GdkPixbuf, GLib, Gtk
from vimiv.helpers import get_float_from_str
from vimiv.fileactions import is_animation


class Image(object):
    """Image class for vimiv.

    Includes the scrollable window with the image and all actions that apply
    to it.

    Attributes:
        app: The main vimiv class to interact with.
        scrolled_win: Gtk.ScrollableWindow for the image.
        viewport: Gtk.Viewport to be able to scroll the image.
        image: Gtk.Image containing the actual image Pixbuf.
        animation_toggled: If True, animation is playing.
        autoplay_gifs: If True, autoplay animations.
        fit_image:
            0: Image is user zoomed.
            1: Image is zoomed to fit.
            2: Image is zoomed to fit horizontally.
            3: Image is zoomed to fit vertically.
        overzoom: Float describing the maximum amount to zoom images above
            their default size.
        rescale_svg: If True rescale vector graphics when zooming.
        shuffle: If True randomly shuffle paths.
        zoom_percent: Percentage to zoom to compared to the original size.
        imsize: Size of the displayed image as a tuple.
        pixbuf_original: Original image.
        pixbuf_iter: Iter of displayed animation.
        timer_id: Id of current animation timer.
    """

    def __init__(self, app, settings):
        """Set default values for attributes."""
        self.app = app
        general = settings["GENERAL"]

        # Generate window structure
        # Scrollable window for the image
        self.scrolled_win = Gtk.ScrolledWindow()
        self.scrolled_win.set_hexpand(True)
        self.scrolled_win.set_vexpand(True)

        # Viewport
        self.viewport = Gtk.Viewport()
        self.image = Gtk.Image()
        self.scrolled_win.add(self.viewport)
        self.viewport.add(self.image)
        self.scrolled_win.connect("key_press_event",
                                  self.app["eventhandler"].key_pressed, "IMAGE")

        # Settings
        self.animation_toggled = False
        self.autoplay_gifs = general["autoplay_gifs"]
        self.fit_image = 1  # Checks if the image fits the window somehow
        self.overzoom = general["overzoom"]
        self.rescale_svg = general["rescale_svg"]
        self.shuffle = general["shuffle"]
        self.zoom_percent = 1
        self.imsize = [0, 0]
        self.pixbuf_original = GdkPixbuf.Pixbuf()
        self.pixbuf_iter = GdkPixbuf.PixbufAnimationIter()
        self.timer_id = 0

    def check_for_edit(self, force):
        """Check if an image was edited before moving.

        Args:
            force: If True move and ignore any editing.
        Return:
            0 if no edits were done or force, 1 else.
        """
        if force:
            self.app["manipulate"].manipulations = \
                {"bri": 1, "con": 1, "sha": 1}
            return 0
        elif self.app["manipulate"].manipulations != \
                {"bri": 1, "con": 1, "sha": 1}:
            self.app["statusbar"].message(
                "Image has been edited, add ! to force", "warning")
            return 1
        return 0

    def get_zoom_percent_to_fit(self, fit=1):
        """Get the zoom factor perfectly fitting the image to the window.

        Args:
            fit: See self.fit_image attribute.
        Return:
            Zoom percentage.
        """
        # Size of the file
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()
        # Maximum size respecting overzoom
        max_width = pbo_width * self.overzoom
        max_height = pbo_height * self.overzoom
        # Get scales for "panorama" vs "portrait" image
        w_scale = pbo_width / self.imsize[0]
        h_scale = pbo_height / self.imsize[1]
        scale_width = True if w_scale > h_scale else False
        # Image fits completely even in with overzoom
        if max_width < self.imsize[0] and max_height < self.imsize[1]:
            return self.overzoom
        # Force horizontal fit or "panorama" image
        elif fit == 2 or (scale_width and fit != 3):
            return self.imsize[0] / pbo_width
        # Force vertical fit or "portrait" image
        return self.imsize[1] / pbo_height

    def update(self, update_info=True):
        """Show the final image.

        Args:
            update_info: If True update the statusbar with new information.
        """
        if not self.app.paths:
            return
        # Scale image
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()
        pbf_width = int(pbo_width * self.zoom_percent)
        pbf_height = int(pbo_height * self.zoom_percent)
        # Rescaling of svg
        name = self.app.paths[self.app.index]
        info = GdkPixbuf.Pixbuf.get_file_info(name)[0]
        if info and "svg" in info.get_extensions():
            pixbuf_final = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                self.app.paths[self.app.index], -1, pbf_height, True)
        else:
            pixbuf_final = self.pixbuf_original.scale_simple(
                pbf_width, pbf_height, GdkPixbuf.InterpType.BILINEAR)
        self.image.set_from_pixbuf(pixbuf_final)
        # Update the statusbar if required
        if update_info:
            self.app["statusbar"].update_info()

    def play_gif(self):
        """Run the animation of a gif."""
        self.animation_toggled = True
        self.pixbuf_original = self.pixbuf_iter.get_pixbuf()
        GLib.idle_add(self.update)
        if self.pixbuf_iter.advance():
            # Clear old timer
            if self.timer_id:
                GLib.source_remove(self.timer_id)
            # Add new timer if the gif is not static
            delay = self.pixbuf_iter.get_delay_time()
            self.timer_id = GLib.timeout_add(delay, self.play_gif) \
                if delay >= 0 else 0

    def pause_gif(self):
        """Pause a gif or show initial image."""
        self.animation_toggled = False
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = 0
        else:
            image = self.pixbuf_iter.get_pixbuf()
            self.image.set_from_pixbuf(image)

    def get_available_size(self):
        """Receive size not occupied by other Widgets.

        Substracts other widgets (manipulate, statusbar, library) from window
        size and returns the available size.

        Return:
            Tuple of available size.
        """
        size = self.app["window"].get_size()
        if self.app["library"].grid.is_visible():
            size = (size[0] - self.app["library"].width, size[1])
        if not self.app["statusbar"].hidden:
            size = (size[0], size[1] - self.app["statusbar"].get_bar_height())
        return size

    def zoom_delta(self, zoom_in=True, step=1):
        """Zoom the image by delta percent.

        Args:
            zoom_in: If True zoom in, else zoom out.
        """
        delta = 0.25
        # Allow user steps
        step = self.app["eventhandler"].num_receive(step, True)
        if isinstance(step, str):
            step, err = get_float_from_str(step)
            if err:
                self.app["statusbar"].message(
                    "Argument for zoom must be of type float", "error")
                return
        fallback_zoom = self.zoom_percent
        if zoom_in:
            self.zoom_percent = self.zoom_percent * (1 + delta * step)
        else:
            self.zoom_percent = self.zoom_percent / (1 + delta * step)
        self.catch_unreasonable_zoom_and_update(fallback_zoom)
        self.fit_image = 0

    def zoom_to(self, percent=0, fit=1):
        """Zoom to a given percentage.

        Args:
            percent: Percentage to zoom to.
            fit: See self.fit_image attribute.
        """
        fallback_zoom = self.zoom_percent
        # Catch user zooms
        percent = self.app["eventhandler"].num_receive(percent, True)
        # Given from commandline
        if isinstance(percent, str):
            percent, err = get_float_from_str(percent)
            if err:
                self.app["statusbar"].message(
                    "Argument for zoom must be of type float", "error")
                return
        self.imsize = self.get_available_size()
        # 0 means zoom to fit
        if percent:
            self.zoom_percent = percent
            self.fit_image = 0
        else:
            self.zoom_percent = self.get_zoom_percent_to_fit(fit)
            self.fit_image = fit
        # Catch some unreasonable zooms
        self.catch_unreasonable_zoom_and_update(fallback_zoom)

    def catch_unreasonable_zoom_and_update(self, fallback_zoom):
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
        max_width = min(self.app["window"].get_size()[0] * 10,
                        self.pixbuf_original.get_width() * 20)
        max_height = min(self.app["window"].get_size()[1] * 10,
                         self.pixbuf_original.get_height() * 20)
        # Image too small or too large
        if new_height < min_height or new_width < min_width \
                or new_height > max_height or new_width > max_width:
            message = "Image cannot be zoomed this far"
            self.app["statusbar"].message(message, "warning")
            self.zoom_percent = fallback_zoom
            return
        self.update()

    def center_window(self):
        """Centre the image in the current window."""
        h_adj = Gtk.Scrollable.get_hadjustment(self.viewport)
        h_middle = (h_adj.get_upper() - h_adj.get_lower() - self.imsize[0]) / 2
        h_adj.set_value(h_middle)
        v_adj = Gtk.Scrollable.get_vadjustment(self.viewport)
        v_middle = (v_adj.get_upper() - v_adj.get_lower() - self.imsize[1]) / 2
        v_adj.set_value(v_middle)
        Gtk.Scrollable.set_hadjustment(self.viewport, h_adj)
        Gtk.Scrollable.set_vadjustment(self.viewport, v_adj)

    def scroll(self, direction):
        """Scroll the image.

        Args:
            direction: Direction to scroll in.
        """
        steps = self.app["eventhandler"].num_receive()
        scale = self.zoom_percent / self.get_zoom_percent_to_fit() * 2
        h_adj = Gtk.Scrollable.get_hadjustment(self.viewport)
        h_size = h_adj.get_upper() - h_adj.get_lower() - self.imsize[0]
        h_step = h_size / scale * steps
        v_adj = Gtk.Scrollable.get_vadjustment(self.viewport)
        v_size = v_adj.get_upper() - v_adj.get_lower() - self.imsize[1]
        v_step = v_size / scale * steps
        # To the ends
        if direction == "H":
            h_adj.set_value(0)
        elif direction == "J":
            v_adj.set_value(v_size)
        elif direction == "K":
            v_adj.set_value(0)
        elif direction == "L":
            h_adj.set_value(h_size)
        # By step
        elif direction == "h":
            h_adj.set_value(h_adj.get_value() - h_step)
        elif direction == "j":
            v_adj.set_value(v_adj.get_value() + v_step)
        elif direction == "k":
            v_adj.set_value(v_adj.get_value() - v_step)
        elif direction == "l":
            h_adj.set_value(h_adj.get_value() + h_step)
        Gtk.Scrollable.set_hadjustment(self.viewport, h_adj)
        Gtk.Scrollable.set_vadjustment(self.viewport, v_adj)

    def move_index(self, forward=True, key=None, delta=1, force=False):
        """Move by delta in paths.

        Args:
            forward: If True move forwards. Else move backwards.
            key: If available, move by key.
            delta: Positions to move by.
            force: If True, move regardless of editing image.
        """
        # Check if an image is opened or if it has been edited
        if not self.app.paths or self.app["thumbnail"].toggled or \
                self.check_for_edit(force):
            return
        # Run the simple manipulations
        self.app["manipulate"].run_simple_manipulations()
        # Check for prepended numbers and direction
        if key:
            delta *= self.app["eventhandler"].num_receive()
        if not forward:
            delta *= -1
        self.app.index = (self.app.index + delta) % len(self.app.paths)
        self.fit_image = 1

        # Reshuffle on wrap-around
        if self.shuffle and self.app.index is 0 and delta > 0:
            shuffle(self.app.paths)

        # Load the image at path into self.pixbuf_* and show it
        self.load_image()

        # Info if slideshow returns to beginning
        if self.app["slideshow"].running:
            if self.app.index is self.app["slideshow"].start_index:
                message = "Back at beginning of slideshow"
                self.app["statusbar"].lock = True
                self.app["statusbar"].message(message, "info")
            else:
                self.app["statusbar"].lock = False

        return True  # for the slideshow

    def load_image(self):
        """Load an image using GdkPixbufLoader."""
        path = self.app.paths[self.app.index]
        # Remove old timers and reset scale
        if self.timer_id:
            self.zoom_percent = 1
            self.pause_gif()
        # Load file
        try:
            loader = ImageLoader(self)
            loader.load(path)
        except (PermissionError, FileNotFoundError):
            self.app.paths.remove(path)
            self.move_pos(False)
            self.app["statusbar"].message("File not accessible", "error")

    def move_pos(self, forward=True, force=False):
        """Move to specific position in paths.

        Args:
            forward: If True move forwards. Else move backwards.
            force: If True, move regardless of editing image.
        """
        # Check if image has been edited
        if self.check_for_edit(force):
            return
        max_pos = len(self.app.paths)
        current = self.app.get_pos(force_widget="im")
        # Move to definition by keys or end/beg
        if forward:
            pos = self.app["eventhandler"].num_receive(max_pos)
        else:
            pos = self.app["eventhandler"].num_receive()
        # Catch range
        if pos < 0 or pos > max_pos:
            self.app["statusbar"].message("Unsupported index", "warning")
            return False
        # Do the maths and move
        dif = pos - current - 1
        if self.app["thumbnail"].toggled:
            pos -= 1
            self.app["thumbnail"].move_to_pos(pos)
        else:
            self.move_index(True, False, dif)
        return True

    def toggle_rescale_svg(self):
        """Toggle rescale state of vector images."""
        self.rescale_svg = not self.rescale_svg

    def set_overzoom(self, new_value="1"):
        """Set overzoom of images."""
        new_value, error = get_float_from_str(new_value)
        if error:
            self.app["statusbar"].message(
                "Argument for zoom must be of type float", "error")
            return
        self.overzoom = new_value
        # Update image if it makes sense
        if self.fit_image:
            self.zoom_percent = self.get_zoom_percent_to_fit(self.fit_image)
            self.update()

    def toggle_animation(self):
        """Toggle animation status of Gifs."""
        if self.app.paths and is_animation(self.app.paths[self.app.index]) \
                and not self.app["thumbnail"].toggled:
            if self.animation_toggled:
                self.pause_gif()
            else:
                self.play_gif()


class ImageLoader(object):
    """An image loader for the Image class above.

    Loads images and animations asynchronously.

    Attributes:
        image: Image class above to interact with.
    """

    # Used so the GUI callbacks are only done if the image is still visible
    identifier = 0

    def __init__(self, image):
        """Initialize loader with vimiv's image class."""
        self.image = image

    def load(self, path):
        """Load an image from path."""
        loader = GdkPixbuf.PixbufLoader()
        ImageLoader.identifier += 1
        if is_animation(path):
            loader.connect("area-prepared", self._set_image_anim)
        else:
            loader.connect("area-prepared", self._set_image_pixbuf)
            loader.connect("closed",
                           self._finish_image_pixbuf, ImageLoader.identifier)
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
        self.image.pixbuf_original = loader.get_pixbuf()
        self.image.imsize = self.image.get_available_size()
        self.image.zoom_percent = self.image.get_zoom_percent_to_fit()

    def _finish_image_pixbuf(self, loader, image_id):
        if ImageLoader.identifier == image_id:
            GLib.idle_add(self.image.update)

    def _set_image_anim(self, loader):
        self.image.pixbuf_iter = loader.get_animation().get_iter()
        self.image.pixbuf_original = self.image.pixbuf_iter.get_pixbuf()
        self.image.imsize = self.image.get_available_size()
        self.image.zoom_percent = self.image.get_zoom_percent_to_fit()
        if self.image.autoplay_gifs:
            delay = self.image.pixbuf_iter.get_delay_time()
            self.image.timer_id = GLib.timeout_add(delay, self.image.play_gif) \
                if delay >= 0 else 0
