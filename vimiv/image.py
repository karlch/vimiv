#!/usr/bin/env python
# encoding: utf-8
"""Image part of vimiv."""

import os
from random import shuffle
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from vimiv.helpers import get_float_from_str


class Image(object):
    """Image class for vimiv.

    Includes the scrollable window with the image and all actions that apply
    to it.

    Attributes:
        app: The main vimiv class to interact with.
        scrolled_win: Gtk.ScrollableWindow for the image.
        viewport: Gtk.Viewport to be able to scroll the image.
        image: Gtk.Image containing the actual image Pixbuf.
        animation_toggled: If True play animations.
        fit_image:
            0: Image is user zoomed.
            1: Image is zoomed to fit.
            2: Image is zoomed to fit horizontally.
            3: Image is zoomed to fit vertically.
        trashdir: Directory for all the deleted files.
        overzoom: If True, increase image size up to window size even if images
            are smaller than window.
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
        self.scrolled_win.connect("key_press_event", self.app["keyhandler"].run,
                                  "IMAGE")

        # Settings
        self.animation_toggled = False
        self.fit_image = 1  # Checks if the image fits the window somehow
        self.trashdir = os.path.join(self.app.directory, "Trash")
        self.overzoom = general["overzoom"]
        self.rescale_svg = general["rescale_svg"]
        self.shuffle = general["shuffle"]
        self.zoom_percent = 1
        self.imsize = [0, 0]
        self.is_anim = False
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
        else:
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
        pbo_scale = pbo_width / pbo_height
        # Size of the image to be shown
        w_scale = self.imsize[0] / self.imsize[1]
        stickout = fit > 1

        # Image is completely shown and user doesn't want overzoom
        if (pbo_width < self.imsize[0] and pbo_height < self.imsize[1] and
                not (stickout or self.overzoom)):
            return 1
        # "Portrait" image
        elif (pbo_scale < w_scale and not stickout) or fit == 3:
            return self.imsize[1] / pbo_height
        # "Panorama/landscape" image
        else:
            return self.imsize[0] / pbo_width

    def update(self, update_info=True, update_gif=True):
        """Show the final image.

        Args:
            update_info: If True update the statusbar with new information.
            update_gif: If True update animation status.
        """
        if not self.app.paths:
            return
        # Start playing an animation if it is one
        if self.is_anim and update_gif:
            if not self.animation_toggled:
                delay = self.pixbuf_iter.get_delay_time()
                self.timer_id = GLib.timeout_add(delay, self.play_gif)
                self.play_gif()
            else:
                self.pause_gif()
        # Otherwise scale the image
        else:
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
        image = self.pixbuf_iter.get_pixbuf()
        self.image.set_from_pixbuf(image)
        if self.pixbuf_iter.advance():
            GLib.source_remove(self.timer_id)
            delay = self.pixbuf_iter.get_delay_time()
            # Do not animate static gifs
            self.timer_id = GLib.timeout_add(delay, self.play_gif) \
                if delay >= 0 else 0

    def pause_gif(self):
        """Pause a gif or show initial image."""
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
            size = (size[0], size[1]
                    - self.app["statusbar"].separator.get_margin_top() - 2)
        return size

    def zoom_delta(self, zoom_in=True, step=1):
        """Zoom the image by delta percent.

        Args:
            zoom_in: If True zoom in, else zoom out.
        """
        delta = 0.25
        if self.is_anim:
            self.app["statusbar"].message("Zoom not supported for gif files",
                                          "warning")
        else:
            # Allow user steps
            if self.app["keyhandler"].num_str:
                step = self.app["keyhandler"].num_str
                self.app["keyhandler"].num_clear()
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

    def zoom_to(self, percent, fit=1):
        """Zoom to a given percentage.

        Args:
            percent: Percentage to zoom to.
            fit: See self.fit_image attribute.
        """
        if self.is_anim:
            self.app["statusbar"].message("Zoom not supported for gif files",
                                          "warning")
            return
        fallback_zoom = self.zoom_percent
        # Catch user zooms
        if self.app["keyhandler"].num_str:
            percent = self.app["keyhandler"].num_str
            self.app["keyhandler"].num_clear()
        # Either num_str or given from commandline
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
        """Catch zooms unreasonable zooms otherwise update.

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
            message = "Image cannot be zoomed further"
            self.app["statusbar"].message(message, "warning")
            self.zoom_percent = fallback_zoom
        else:
            self.update(update_gif=False)

    def center_window(self):
        """Centre the image in the current window."""
        # Don't do anything if no images are open
        if not self.app.paths or self.app["thumbnail"].toggled:
            return
        # Get center of adjustments and set them
        h_adj = Gtk.Scrollable.get_hadjustment(self.viewport)
        h_middle = (h_adj.get_upper() - h_adj.get_lower() - self.imsize[0]) / 2
        h_adj.set_value(h_middle)
        v_adj = Gtk.Scrollable.get_vadjustment(self.viewport)
        v_middle = (v_adj.get_upper() - v_adj.get_lower() - self.imsize[1]) / 2
        v_adj.set_value(v_middle)
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
        if key and self.app["keyhandler"].num_str:
            delta *= int(self.app["keyhandler"].num_str)
            self.app["keyhandler"].num_clear()
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
        # Remove old timers
        if self.timer_id:
            self.pause_gif()
        # Load file
        try:
            info = GdkPixbuf.Pixbuf.get_file_info(path)[0]
            if "gif" in info.get_extensions():
                self.is_anim = True
                anim = GdkPixbuf.PixbufAnimation.new_from_file(path)
                self.pixbuf_iter = anim.get_iter()
            else:
                self.is_anim = False
                self.pixbuf_original = GdkPixbuf.Pixbuf.new_from_file(path)
                self.imsize = self.get_available_size()
                self.zoom_percent = self.get_zoom_percent_to_fit()
            self.update(update_info=True)
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
        if self.app["keyhandler"].num_str:
            pos = int(self.app["keyhandler"].num_str)
            self.app["keyhandler"].num_clear()
        elif forward:
            pos = max_pos
        else:
            pos = 1
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

    def toggle_overzoom(self):
        """Toggle overzoom of images."""
        self.overzoom = not self.overzoom

    def toggle_animation(self):
        """Toggle animation status of Gifs."""
        if self.app.paths and not self.app["thumbnail"].toggled:
            self.animation_toggled = not self.animation_toggled
            self.update()
