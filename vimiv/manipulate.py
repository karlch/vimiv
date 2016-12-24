#!/usr/bin/env python
# encoding: utf-8
"""Manipulate part for vimiv."""

import os
from threading import Thread
from PIL import Image, ImageEnhance
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from vimiv import imageactions
from vimiv.fileactions import move_to_trash


class Manipulate(object):
    """Manipulate class for vimiv.

    Includes the manipulation toolbar, all the actions that apply to it and all
    the other image manipulations like rotate, flip, and so on.

    Attributes:
        app: The main vimiv application to interact with.
        manipulations: Dictionary of possible manipulations. Includes
            brightness, contrast and sharpness.
        scrolled_win: Gtk.ScrolledWindow for the widgets so they are accessible
            regardless of window size.
        scale_bri: Gtk.Scale for brightness.
        scale_con: Gtk.Scale for contrast.
        scale_sha: Gtk.Scale for sharpness.
        running_threads: List of running threads.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        self.app = app

        # Settings
        self.manipulations = {"bri": 1, "con": 1, "sha": 1}
        self.pil_image = Image
        self.pil_thumb = Image

        # A scrollable window so all tools are always accessible
        self.scrolled_win = Gtk.ScrolledWindow()
        # A grid in which everything gets packed
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_border_width(6)
        grid.connect("key_press_event", self.app["keyhandler"].run,
                     "MANIPULATE")
        self.scrolled_win.add(grid)

        # Sliders
        self.scale_bri = Gtk.Scale()
        self.scale_bri.connect("value-changed", self.value_slider, "bri")
        self.scale_con = Gtk.Scale()
        self.scale_con.connect("value-changed", self.value_slider, "con")
        self.scale_sha = Gtk.Scale()
        self.scale_sha.connect("value-changed", self.value_slider, "sha")

        # Set some properties
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            scale.set_range(-127, 127)
            scale.set_size_request(120, 20)
            scale.set_value(0)
            scale.set_digits(0)

        # Labels
        bri_label = Gtk.Label()
        bri_label.set_markup("\n<b>Bri</b>")
        con_label = Gtk.Label()
        con_label.set_markup("\n<b>Con</b>")
        sha_label = Gtk.Label()
        sha_label.set_markup("\n<b>Sha</b>")

        # Dummy grid as separator
        separator = Gtk.Grid()
        separator.set_hexpand(True)

        # Buttons
        button_yes = Gtk.Button(label="Accept")
        button_yes.connect("clicked", self.button_clicked, True)
        button_yes.set_size_request(80, 20)
        button_no = Gtk.Button(label="Cancel")
        button_no.connect("clicked", self.button_clicked, False)
        button_no.set_size_request(80, 20)

        # Pack everything into the grid
        for item in [bri_label, self.scale_bri, con_label, self.scale_con,
                     sha_label, self.scale_sha, separator, button_yes,
                     button_no]:
            grid.add(item)

        self.running_threads = []

    def delete(self):
        """Delete all marked images or the current one."""
        # Get all images
        images = self.get_manipulated_images("Deleted")
        self.app["mark"].marked = []
        # Delete all images
        for i, im in enumerate(images):
            message = ""
            if not os.path.exists(im):
                message = "Image %s does not exist" % (im)
            elif os.path.isdir(im):
                message = "Deleting directories is not supported"
            if message:
                self.app["statusbar"].err_message(message)
                images.remove(i)
        move_to_trash(images, self.app["image"].trashdir)

        # Reload stuff if needed
        if self.app["library"].grid.is_visible():
            if self.app.get_pos():
                self.app["library"].remember_pos(os.getcwd(),
                                                 self.app.get_pos() - 1)
            self.app["library"].reload(os.getcwd())
        if self.app["image"].scrolled_win.is_focus():
            del self.app.paths[self.app.index]
            if self.app.paths:
                self.app["image"].load_image()
            else:
                # No more images in this directory -> focus parent in library
                self.app["library"].move_up()
                self.app["library"].focus(True)
                self.app["statusbar"].err_message("No more images")

    def get_manipulated_images(self, message):
        """Return the images which should be manipulated.

        Either the currently focused image or all marked images.

        Args:
            message: Message to display when acting on marked images.
        """
        images = []
        # Add the image shown
        if not self.app["mark"].marked and not self.app["thumbnail"].toggled:
            if self.app["library"].treeview.is_focus():
                images.append(
                    os.path.abspath(self.app.get_pos(True)))
            else:
                images.append(self.app.paths[self.app.index])
        # Add all marked images
        else:
            images = self.app["mark"].marked
            # Abuse err_message to simply display information about what is done
            if len(images) == 1:
                err = "%s %d marked image" % (message, len(images))
            else:
                err = "%s %d marked images" % (message, len(images))
            self.app["statusbar"].err_message(err)
        # Delete all thumbnails of manipulated images
        thumbnails = os.listdir(self.app["thumbnail"].directory)
        for im in images:
            thumb = ".".join(im.split(".")[:-1]) + ".thumbnail" + ".png"
            thumb = os.path.basename(thumb)
            if thumb in thumbnails:
                thumb = os.path.join(self.app["thumbnail"].directory, thumb)
                os.remove(thumb)

        return images

    def rotate(self, cwise, rotate_file=True):
        """Rotate the displayed image and call thread to rotate files.

        Args:
            cwise: Rotate image 90 * cwise degrees.
            rotate_file: If True call thread to rotate files.
        """
        try:
            cwise = int(cwise)
            images = self.get_manipulated_images("Rotated")
            cwise = cwise % 4
            # Rotate the image shown
            if self.app.paths[self.app.index] in images:
                self.app["image"].pixbuf_original = \
                    self.app["image"].pixbuf_original.rotate_simple(
                        (90 * cwise))
                self.app["image"].update(False)
            if rotate_file:
                # Rotate all files in external thread
                rotate_thread = Thread(target=self.thread_for_rotate,
                                       args=(images, cwise))
                self.running_threads.append(rotate_thread)
                rotate_thread.start()
        except:
            self.app["statusbar"].err_message(
                "Warning: Object cannot be rotated")

    def thread_for_rotate(self, images, cwise):
        """Rotate all image files in an extra thread.

        Args:
            images: List of images to rotate.
            cwise: Rotate image 90 * cwise degrees.
        """
        try:
            # Finish older manipulate threads first
            while len(self.running_threads) > 1:
                self.running_threads[0].join()
            imageactions.rotate_file(images, cwise)
            if self.app["thumbnail"].toggled:
                for image in images:
                    self.app["thumbnail"].reload(
                        image, self.app.paths.index(image))
        except:
            self.app["statusbar"].err_message("Error: Rotation of file failed")
        self.running_threads.pop(0)

    def flip(self, horizontal, flip_file=True):
        """Flip the displayed image and call thread to flip files.

        Args:
            horizontal: If 1 flip horizontally. Else vertically.
            rotate_file: If True call thread to rotate files.
        """
        try:
            horizontal = int(horizontal)
            images = self.get_manipulated_images("Flipped")
            # Flip the image shown
            if self.app.paths[self.app.index] in images:
                self.app["image"].pixbuf_original = \
                    self.app["image"].pixbuf_original.flip(horizontal)
                self.app["image"].update(False)
            if flip_file:
                # Flip all files in an extra thread
                flip_thread = Thread(target=self.thread_for_flip,
                                     args=(images, horizontal))
                self.running_threads.append(flip_thread)
                flip_thread.start()
        except:
            self.app["statusbar"].err_message(
                "Warning: Object cannot be flipped")

    def thread_for_flip(self, images, horizontal):
        """Flip all image files in an extra thread.

        Args:
            images: List of images to rotate.
            horizontal: If 1 flip horizontally. Else vertically.
        """
        try:
            # Finish older manipulate threads first
            while len(self.running_threads) > 1:
                self.running_threads[0].join()
            imageactions.flip_file(images, horizontal)
            if self.app["thumbnail"].toggled:
                for image in images:
                    self.app["thumbnail"].reload(
                        image, self.app.paths.index(image))
        except:
            self.app["statusbar"].err_message("Error: Flipping of file failed")
        self.running_threads.pop(0)

    def rotate_auto(self):
        """Autorotate all pictures in the current pathlist."""
        amount, method = imageactions.autorotate(self.app.paths)
        if amount:
            self.app["image"].load_image()
            message = "Autorotated %d image(s) using %s." % (amount, method)
        else:
            message = "No image rotated. Tried using %s." % (method)
        self.app["statusbar"].err_message(message)

    def toggle(self):
        """Toggle the manipulation bar."""
        if self.scrolled_win.is_visible():
            self.scrolled_win.hide()
            self.app["image"].scrolled_win.grab_focus()
            self.app["statusbar"].update_info()
        elif self.app.paths and not(self.app["thumbnail"].toggled or
                                    self.app["library"].treeview.is_focus()):
            if os.path.islink(self.app.paths[self.app.index]):
                self.app["statusbar"].err_message(
                    "Manipulating symbolik links is not supported")
                return
            if self.app["image"].is_anim:
                self.app["statusbar"].err_message(
                    "Manipulating Gifs is not supported")
            else:
                self.scrolled_win.show()
                self.scale_bri.grab_focus()
                self.app["statusbar"].update_info()
                # Create PIL image to work with
                size = self.app["image"].imsize
                self.pil_image = Image.open(self.app.paths[self.app.index])
                self.pil_thumb = Image.open(self.app.paths[self.app.index])
                # pylint: disable=no-member
                self.pil_thumb.thumbnail(size, Image.ANTIALIAS)
        else:
            if self.app["thumbnail"].toggled:
                self.app["statusbar"].err_message(
                    "Manipulate not supported in thumbnail mode")
            elif self.app["library"].treeview.is_focus():
                self.app["statusbar"].err_message(
                    "Manipulate not supported in library")
            else:
                self.app["statusbar"].err_message("No image open to edit")

    def manipulate_image(self, apply_to_file=False):
        """Apply manipulations to image.

        Manipulations are the three sliders for brightness, contrast and
        sharpness. They are applied to a thumbnail by default and can act on the
        real image.

        Args:
            real: If True, apply manipulations to the real image.
        """
        if apply_to_file:
            imfile = self.pil_image
        else:
            imfile = self.pil_thumb
        # Apply Brightness, Contrast and Sharpness
        enhanced_im = ImageEnhance.Brightness(imfile).enhance(
            self.manipulations["bri"])
        enhanced_im = ImageEnhance.Contrast(enhanced_im).enhance(
            self.manipulations["con"])
        enhanced_im = ImageEnhance.Sharpness(enhanced_im).enhance(
            self.manipulations["sha"])
        # On real file save data to file
        if apply_to_file:
            imageactions.save_image(enhanced_im, self.app.paths[self.app.index])
        # Load Pixbuf from PIL data
        data = enhanced_im.tobytes()
        g_data = GLib.Bytes.new(data)
        # pylint: disable=no-member
        w, h = imfile.size
        if imfile.mode == 'RGBA':
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                g_data, GdkPixbuf.Colorspace.RGB, True, 8, w, h, 4 * w)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                g_data, GdkPixbuf.Colorspace.RGB, False, 8, w, h, 3 * w)
        # Show the edited pixbuf
        self.app["image"].pixbuf_original = pixbuf
        self.app["image"].update()
        self.app["image"].zoom_to(0)

    def value_slider(self, slider, name):
        """Set value of self.manipulations according to slider value.

        Args:
            slider: Gtk.Scale on which to operate.
            name: Name of slider to operate on.
        """
        val = slider.get_value()
        val = (val + 127) / 127
        # Change brightness, contrast or sharpness
        self.manipulations[name] = val
        # Run the manipulation function
        self.manipulate_image()

    def focus_slider(self, name):
        """Set focus on one of the three sliders.

        Args:
            name: Name of slider to focus.
        """
        if name == "bri":
            self.scale_bri.grab_focus()
        elif name == "con":
            self.scale_con.grab_focus()
        else:
            self.scale_sha.grab_focus()

    def change_slider(self, step=1):
        """Change the value of the currently focused slider.

        Args:
            dec: If True decrease the value.
            large: If True use large step (10) instead of small one (1)
        """
        try:
            step = int(step)
        except:
            self.app["statusbar"].err_message("Error: Invalid step")
            return
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            if scale.is_focus():
                val = scale.get_value()
                if self.app["keyhandler"].num_str:
                    step = int(self.app["keyhandler"].num_str)
                    self.app["keyhandler"].num_clear()
                val += step
                scale.set_value(val)

    def button_clicked(self, button, accept=False):
        """Finish manipulate mode.

        Args:
            button: Gtk.Button that was clicked.
            accept: If True apply changes to image file. Else discard them.
        """
        # Apply changes
        if accept:
            self.manipulate_image(True)
        # Reset all the manipulations
        self.manipulations = {"bri": 1, "con": 1, "sha": 1}
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            scale.set_value(0)
        # Show the original image
        self.app["image"].user_zoomed = False
        self.app["image"].load_image()
        # Done
        self.toggle()
        self.app["statusbar"].update_info()

    def cmd_edit(self, manipulation, num="0"):
        """Run the specified manipulation.

        Args:
            manipulation: Name of manipulation to run.
            num: Value for setting the slider.
        """
        if not self.scrolled_win.is_visible():
            if not self.app.paths:
                self.app["statusbar"].err_message("No image to manipulate")
                return
            else:
                self.toggle()
        self.focus_slider(manipulation)
        self.app["keyhandler"].num_str = num
        execstr = "self.scale_" + manipulation + \
            ".set_value(int(self.app['keyhandler'].num_str))"
        exec(execstr)
        self.app["keyhandler"].num_str = ""
