#!/usr/bin/env python
# encoding: utf-8
""" Image part of vimiv """

import os
from random import shuffle
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib


class Image(object):
    """ Image class for vimiv
        includes the scrollable window with the image and all actions that apply
        to it """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Generate window structure
        # Scrollable window for the image
        self.scrolled_win = Gtk.ScrolledWindow()
        self.vimiv.hbox.pack_end(self.scrolled_win, True, True, 0)

        # Viewport
        self.viewport = Gtk.Viewport()
        self.viewport.set_shadow_type(Gtk.ShadowType.NONE)
        self.scrolled_win.add(self.viewport)
        self.image = Gtk.Image()
        self.viewport.add(self.image)
        self.scrolled_win.connect("key_press_event",
                                  self.vimiv.keyhandler.run,
                                  "IMAGE")

        # Settings
        self.animation_toggled = False
        self.user_zoomed = False  # checks if the user manually zoomed the
        self.trashdir = os.path.join(self.vimiv.directory, "Trash")
        self.overzoom = general["overzoom"]
        self.rescale_svg = general["rescale_svg"]
        self.shuffle = general["shuffle"]
        self.zoom_percent = 1
        self.imsize = [0, 0]
        self.pixbuf_original = GdkPixbuf.PixbufAnimation

    def check_for_edit(self, force):
        """ Checks if an image was edited before moving """
        if self.vimiv.paths:
            if "EDIT" in self.vimiv.paths[self.vimiv.index]:
                if force:
                    self.vimiv.manipulate.button_clicked(False)
                    return 0
                else:
                    self.vimiv.statusbar.err_message(
                        "Image has been edited, add ! to force")
                    return 1

    def get_zoom_percent(self, z_width=False, z_height=False):
        """ returns the current zoom factor """
        # Size of the file
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()
        pbo_scale = pbo_width / pbo_height
        # Size of the image to be shown
        w_scale = self.imsize[0] / self.imsize[1]
        stickout = z_width | z_height

        # Image is completely shown and user doesn't want overzoom
        if (pbo_width < self.imsize[0] and pbo_height < self.imsize[1] and
                not (stickout or self.overzoom)):
            return 1
        # "Portrait" image
        elif (pbo_scale < w_scale and not stickout) or z_height:
            return self.imsize[1] / pbo_height
        # "Panorama/landscape" image
        else:
            return self.imsize[0] / pbo_width

    def update(self, update_info=True, update_gif=True):
        """ Show the final image """
        if not self.vimiv.paths:
            return
        pbo_width = self.pixbuf_original.get_width()
        pbo_height = self.pixbuf_original.get_height()

        # pylint:disable=no-member
        try:  # If possible scale the image
            pbf_width = int(pbo_width * self.zoom_percent)
            pbf_height = int(pbo_height * self.zoom_percent)
            # Rescaling of svg
            ending = os.path.basename(
                self.vimiv.paths[self.vimiv.index]).split(".")[-1]
            if ending == "svg" and self.rescale_svg:
                pixbuf_final = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    self.vimiv.paths[self.vimiv.index], -1, pbf_height, True)
            else:
                pixbuf_final = self.pixbuf_original.scale_simple(
                    pbf_width, pbf_height, GdkPixbuf.InterpType.BILINEAR)
            self.image.set_from_pixbuf(pixbuf_final)
        except:  # If not it must me an animation
            # TODO actual pause and play of Gifs
            self.zoom_percent = 1
            if update_gif:
                if not self.animation_toggled:
                    self.image.set_from_animation(self.pixbuf_original)
                else:
                    pixbuf_final = self.pixbuf_original.get_static_image()
                    self.image.set_from_pixbuf(pixbuf_final)
        # Update the statusbar if required
        if update_info:
            self.vimiv.statusbar.update_info()

    def get_size(self):
        """ Returns the size of the image depending on what other widgets
        are visible and if fullscreen or not """
        if self.vimiv.window.fullscreen:
            size = self.vimiv.screensize
        else:
            size = self.vimiv.get_size()
        if self.vimiv.library.toggled:
            size = (size[0] - self.vimiv.library.width, size[1])
        if not self.vimiv.statusbar.hidden:
            size = (size[0], size[1] - self.vimiv.statusbar.size - 24)
        return size

    def zoom_delta(self, delta):
        """ Zooms the image by delta percent """
        if self.vimiv.thumbnail.toggled:
            return
        try:
            self.zoom_percent = self.zoom_percent * (1 + delta)
            # Catch some unreasonable zooms
            if (self.pixbuf_original.get_height() * self.zoom_percent < 50 or
                    self.pixbuf_original.get_height() * self.zoom_percent >
                    self.vimiv.screensize[0] * 5):
                raise ValueError
            self.user_zoomed = True
            self.update(update_gif=False)
        except:
            self.zoom_percent = self.zoom_percent / (1 + delta)
            message = "Warning: Object cannot be zoomed (further)"
            self.vimiv.statusbar.err_message(message)

    def zoom_to(self, percent, z_width=False, z_height=False):
        """ Zooms to a given percentage """
        if self.vimiv.thumbnail.toggled:
            return
        before = self.zoom_percent
        self.user_zoomed = False
        # Catch user zooms
        if self.vimiv.keyhandler.num_str:
            self.user_zoomed = True
            percent = self.vimiv.keyhandler.num_str
            # If prefixed with a zero invert value
            try:
                if percent[0] == "0":
                    percent = 1 / float(percent[1:])
                else:
                    percent = float(percent)
            except:
                self.vimiv.statusbar.err_message(
                    "Error: Zoom percentage not parseable")
                return
            self.vimiv.keyhandler.num_str = ""
        try:
            self.imsize = self.get_size()
            self.zoom_percent = (percent if percent
                                 else self.get_zoom_percent(z_width, z_height))
            # Catch some unreasonable zooms
            if (self.pixbuf_original.get_height() * self.zoom_percent < 5 or
                    self.pixbuf_original.get_height() * self.zoom_percent >
                    self.vimiv.screensize[0] * 5):
                self.zoom_percent = before
                raise ValueError
            self.update(update_gif=False)
        except:
            self.vimiv.statusbar.err_message(
                "Warning: Object cannot be zoomed (further)")

    def center_window(self):
        """ Centers the image in the current window """
        # Don't do anything if no images are open
        if not self.vimiv.paths or self.vimiv.thumbnail.toggled:
            return
        # Vertical
        pbo_height = self.pixbuf_original.get_height()
        vadj = self.viewport.get_vadjustment().get_value()
        vact = self.zoom_percent * pbo_height
        diff = vact - self.imsize[1]
        if diff > 0:
            toscroll = (diff - 2 * vadj) / 2
            Gtk.Adjustment.set_step_increment(
                self.viewport.get_vadjustment(), toscroll)
            self.scrolled_win.emit('scroll-child',
                                   Gtk.ScrollType.STEP_FORWARD, False)
            # Reset scrolling
            Gtk.Adjustment.set_step_increment(self.viewport.get_vadjustment(),
                                              100)
        # Horizontal
        pbo_width = self.pixbuf_original.get_width()
        hadj = self.viewport.get_hadjustment().get_value()
        hact = self.zoom_percent * pbo_width
        if diff > 0:
            diff = hact - self.imsize[0]
            toscroll = (diff - 2 * hadj) / 2
            Gtk.Adjustment.set_step_increment(
                self.viewport.get_hadjustment(), toscroll)
            self.scrolled_win.emit('scroll-child',
                                   Gtk.ScrollType.STEP_FORWARD, True)
            # Reset scrolling
            Gtk.Adjustment.set_step_increment(self.viewport.get_hadjustment(),
                                              100)

    def move_index(self, forward=True, key=False, delta=1, force=False):
        """ Move by delta in the path """
        # Check if an image is opened
        if not self.vimiv.paths or self.vimiv.thumbnail.toggled:
            return
        # Check if image has been edited
        if self.check_for_edit(force):
            return
        # Check for prepended numbers
        if key and self.vimiv.keyhandler.num_str:
            delta *= int(self.vimiv.keyhandler.num_str)
        # Forward or backward
        if not forward:
            delta *= -1
        self.vimiv.index = (self.vimiv.index + delta) % len(self.vimiv.paths)
        self.user_zoomed = False

        # Reshuffle on wrap-around
        if self.shuffle and self.vimiv.index is 0 and delta > 0:
            shuffle(self.vimiv.paths)

        path = self.vimiv.paths[self.vimiv.index]
        try:
            if not os.path.exists(path):
                self.vimiv.manipulate.delete()
                return
            else:
                self.pixbuf_original = GdkPixbuf.PixbufAnimation.new_from_file(
                    path)
            if self.pixbuf_original.is_static_image():
                self.pixbuf_original = self.pixbuf_original.get_static_image()
                self.imsize = self.get_size()
                self.zoom_percent = self.get_zoom_percent()
            else:
                self.zoom_percent = 1
            # If one simply reloads the file the info shouldn't be updated
            if delta:
                self.update()
            else:
                self.update(False)

        except GLib.Error:  # File not accessible
            self.vimiv.paths.remove(path)
            self.vimiv.statusbar.err_message("Error: file not accessible")
            self.move_pos(False)

        # Info if slideshow returns to beginning
        if self.vimiv.slideshow.running:
            if self.vimiv.index is self.vimiv.slideshow.start_index:
                message = "Info: back at beginning of slideshow"
                self.vimiv.statusbar.lock = True
                self.vimiv.statusbar.err_message(message)
            else:
                self.vimiv.statusbar.lock = False

        self.vimiv.keyhandler.num_clear()
        return True  # for the slideshow

    def move_pos(self, forward=True, force=False):
        """ Move to pos in path """
        # Check if image has been edited (might be gone by now -> try)
        try:
            if self.check_for_edit(force):
                raise ValueError
        except:
            return
        max_pos = len(self.vimiv.paths)
        if self.vimiv.thumbnail.toggled:
            current = self.vimiv.thumbnail.pos % len(self.vimiv.paths)
            max_pos = max_pos - len(self.vimiv.thumbnail.errorpos)
        else:
            current = (self.vimiv.index) % len(self.vimiv.paths)
        # Move to definition by keys or end/beg
        if self.vimiv.keyhandler.num_str:
            pos = int(self.vimiv.keyhandler.num_str)
        elif forward:
            pos = max_pos
        else:
            pos = 1
        # Catch exceptions
        try:
            current = int(current)
            max_pos = int(max_pos)
            if pos < 0 or pos > max_pos:
                raise ValueError
        except:
            self.vimiv.statusbar.err_message("Warning: Unsupported index")
            return False
        # Do the math and move
        dif = pos - current - 1
        if self.vimiv.thumbnail.toggled:
            pos -= 1
            self.vimiv.thumbnail.pos = pos
            path = Gtk.TreePath.new_from_string(str(pos))
            self.vimiv.thumbnail.iconview.select_path(path)
            curthing = self.vimiv.thumbnail.iconview.get_cells()[0]
            self.vimiv.thumbnail.iconview.set_cursor(path, curthing, False)
            if forward:
                self.scrolled_win.emit('scroll-child',
                                       Gtk.ScrollType.END, False)
            else:
                self.scrolled_win.emit('scroll-child',
                                       Gtk.ScrollType.START, False)
        else:
            self.move_index(True, False, dif)
            self.user_zoomed = False

        self.vimiv.keyhandler.num_clear()
        return True

    def toggle_rescale_svg(self):
        self.rescale_svg = not self.rescale_svg

    def toggle_overzoom(self):
        self.overzoom = not self.overzoom

    def toggle_animation(self):
        """ Toggles animation status of Gifs """
        if self.vimiv.paths and not self.vimiv.thumbnail.toggled:
            self.animation_toggled = not self.animation_toggled
            self.update()
