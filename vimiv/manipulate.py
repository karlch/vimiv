#!/usr/bin/env python
# encoding: utf-8
"""Manipulate part for vimiv."""

import os
from threading import Thread
from PIL import Image
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from vimiv import imageactions
from vimiv.fileactions import move_to_trash


class Manipulate(object):
    """Manipulate class for vimiv.

    Includes the manipulation toolbar, all the actions that apply to it and all
    the other image manipulations like rotate, flip, and so on.

    Attributes:
        vimiv: The main vimiv class to interact with.
        toggled: If True the manipulation bar is visible.
        manipulations. List of possible manipulations. Includes brightness,
            contrast, sharpness and optimize.
        scrolled_win: Gtk.ScrolledWindow for the widgets so they are accessible
            regardless of window size.
        scale_bri: Gtk.Scale for brightness.
        scale_con: Gtk.Scale for contrast.
        scale_sha: Gtk.Scale for sharpness.
        running_threads: List of running threads.
    """

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv

        # Settings
        self.toggled = False
        self.manipulations = [1, 1, 1, False]

        # A scrollable window so all tools are always accessible
        self.scrolled_win = Gtk.ScrolledWindow()
        # A grid in which everything gets packed
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_border_width(6)
        grid.connect("key_press_event", self.vimiv.keyhandler.run, "MANIPULATE")
        self.scrolled_win.add_with_viewport(grid)

        # A list to save the changes being done
        self.manipulations = [1, 1, 1, False]

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
        button_opt = Gtk.Button(label="Optimize")
        button_opt.connect("clicked", self.button_opt_clicked)
        button_opt.set_size_request(80, 20)

        # Pack everything into the grid
        for item in [bri_label, self.scale_bri, con_label, self.scale_con,
                     sha_label, self.scale_sha, separator, button_opt,
                     button_yes, button_no]:
            grid.add(item)

        self.running_threads = []

    def delete(self):
        """Delete all marked images or the current one."""
        # Get all images
        images = self.get_manipulated_images("Deleted")
        self.vimiv.mark.marked = []
        # Delete all images
        for i, im in enumerate(images):
            message = ""
            if not os.path.exists(im):
                message = "Image %s does not exist" % (im)
            elif os.path.isdir(im):
                message = "Deleting directories is not supported"
            if message:
                self.vimiv.statusbar.err_message(message)
                images.remove(i)
        move_to_trash(images)

        # Reload stuff if needed
        if self.vimiv.library.grid.is_visible():
            if self.vimiv.get_pos():
                self.vimiv.library.remember_pos(os.getcwd(),
                                                self.vimiv.get_pos() - 1)
            self.vimiv.library.reload(os.getcwd())
        if self.vimiv.image.scrolled_win.is_focus():
            del self.vimiv.paths[self.vimiv.index]
            if self.vimiv.paths:
                self.vimiv.image.move_index(delta=0)
            else:
                # No more images in this directory -> focus parent in library
                self.vimiv.library.move_up()
                self.vimiv.library.focus(True)
                self.vimiv.statusbar.err_message("No more images")

    def get_manipulated_images(self, message):
        """Return the images which should be manipulated.

        Either the currently focused image or all marked images.

        Args:
            message: Message to display when acting on marked images.
        """
        images = []
        # Add the image shown
        if not self.vimiv.mark.marked and not self.vimiv.thumbnail.toggled:
            if self.vimiv.library.treeview.is_focus():
                images.append(
                    os.path.abspath(self.vimiv.get_pos(True)))
            else:
                images.append(self.vimiv.paths[self.vimiv.index])
        # Add all marked images
        else:
            images = self.vimiv.mark.marked
            # Abuse err_message to simply display information about what is done
            if len(images) == 1:
                err = "%s %d marked image" % (message, len(images))
            else:
                err = "%s %d marked images" % (message, len(images))
            self.vimiv.statusbar.err_message(err)
        # Delete all thumbnails of manipulated images
        thumbnails = os.listdir(self.vimiv.thumbnail.directory)
        for im in images:
            thumb = ".".join(im.split(".")[:-1]) + ".thumbnail" + ".png"
            thumb = os.path.basename(thumb)
            if thumb in thumbnails:
                thumb = os.path.join(self.vimiv.thumbnail.directory, thumb)
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
            if self.vimiv.paths[self.vimiv.index] in images:
                self.vimiv.image.pixbuf_original = \
                    self.vimiv.image.pixbuf_original.rotate_simple((90 * cwise))
                self.vimiv.image.update(False)
            if rotate_file:
                # Rotate all files in external thread
                rotate_thread = Thread(target=self.thread_for_rotate,
                                       args=(images, cwise))
                self.running_threads.append(rotate_thread)
                rotate_thread.start()
        except:
            self.vimiv.statusbar.err_message(
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
            if self.vimiv.thumbnail.toggled:
                for image in images:
                    self.vimiv.thumbnail.reload(
                        image, self.vimiv.paths.index(image))
        except:
            self.vimiv.statusbar.err_message("Error: Rotation of file failed")
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
            if self.vimiv.paths[self.vimiv.index] in images:
                self.vimiv.image.pixbuf_original = \
                    self.vimiv.image.pixbuf_original.flip(horizontal)
                self.vimiv.image.update(False)
            if flip_file:
                # Flip all files in an extra thread
                flip_thread = Thread(target=self.thread_for_flip,
                                     args=(images, horizontal))
                self.running_threads.append(flip_thread)
                flip_thread.start()
        except:
            self.vimiv.statusbar.err_message(
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
            if self.vimiv.thumbnail.toggled:
                for image in images:
                    self.vimiv.thumbnail.reload(
                        image, self.vimiv.paths.index(image))
        except:
            self.vimiv.statusbar.err_message("Error: Flipping of file failed")
        self.running_threads.pop(0)

    def rotate_auto(self):
        """Autorotate all pictures in the current pathlist."""
        amount, method = imageactions.autorotate(self.vimiv.paths)
        if amount:
            self.vimiv.image.move_index(True, False, 0)
            message = "Autorotated %d image(s) using %s." % (amount, method)
        else:
            message = "No image rotated. Tried using %s." % (method)
        self.vimiv.statusbar.err_message(message)

    def toggle(self):
        """Toggle the manipulation bar."""
        if self.toggled:
            self.toggled = False
            self.scrolled_win.hide()
            self.vimiv.image.scrolled_win.grab_focus()
            self.vimiv.statusbar.update_info()
        elif self.vimiv.paths and not(self.vimiv.thumbnail.toggled or
                                      self.vimiv.library.treeview.is_focus()):
            if os.path.islink(self.vimiv.paths[self.vimiv.index]):
                self.vimiv.statusbar.err_message(
                    "Manipulating symbolik links is not supported")
                return
            try:
                self.vimiv.image.pixbuf_original.is_static_image()
                self.vimiv.statusbar.err_message(
                    "Manipulating Gifs is not supported")
            except:
                self.toggled = True
                self.scrolled_win.show()
                self.scale_bri.grab_focus()
                self.vimiv.statusbar.update_info()
        else:
            if self.vimiv.thumbnail.toggled:
                self.vimiv.statusbar.err_message(
                    "Manipulate not supported in thumbnail mode")
            elif self.vimiv.library.treeview.is_focus():
                self.vimiv.statusbar.err_message(
                    "Manipulate not supported in library")
            else:
                self.vimiv.statusbar.err_message("No image open to edit")

    def manipulate_image(self, real=""):
        """Apply manipulations to image.

        Manipulations are the three sliders for brightness, contrast and
        sharpness and optimize from ImageMagick. They are applied to a thumbnail
        by default and can act on the real image.

        Args:
            real: If set, apply manipulations to the real image.
        """
        if real:  # To the actual image?
            orig, out = real, real
        # A thumbnail for higher responsiveness
        elif "-EDIT" not in self.vimiv.paths[self.vimiv.index]:
            with open(self.vimiv.paths[self.vimiv.index], "rb") as image_file:
                im = Image.open(image_file)
                out = "-EDIT.".join(
                    self.vimiv.paths[self.vimiv.index].rsplit(".", 1))
                orig = out.replace("EDIT", "EDIT-ORIG")
                im.thumbnail(self.vimiv.image.imsize, Image.ANTIALIAS)
                imageactions.save_image(im, out)
                self.vimiv.paths[self.vimiv.index] = out
                # Save the original to work with
                imageactions.save_image(im, orig)
        else:
            out = self.vimiv.paths[self.vimiv.index]
            orig = out.replace("EDIT", "EDIT-ORIG")
        # Apply all manipulations
        if imageactions.manipulate_all(orig, out, self.manipulations):
            self.vimiv.statusbar.err_message(
                "Optimize failed. Is imagemagick installed?")
        # Reset optimize so it isn't repeated all the time
        self.manipulations[3] = False

        # Show the edited image
        self.vimiv.image.image.clear()
        self.vimiv.image.pixbuf_original = \
            GdkPixbuf.PixbufAnimation.new_from_file(
                out)
        self.vimiv.image.pixbuf_original = \
            self.vimiv.image.pixbuf_original.get_static_image()
        if not self.vimiv.window.fullscreen:
            self.vimiv.image.imsize = self.vimiv.image.get_available_size()
        self.vimiv.image.zoom_percent = self.vimiv.image.get_zoom_percent()
        self.vimiv.image.update()

    def value_slider(self, slider, name):
        """Set value of self.manipulations according to slider value.

        Args:
            slider: Gtk.Scale on which to operate.
            name: Name of slider to operate on.
        """
        val = slider.get_value()
        val = (val + 127) / 127
        # Change brightness, contrast or sharpness
        if name == "bri":
            self.manipulations[0] = val
        elif name == "con":
            self.manipulations[1] = val
        else:
            self.manipulations[2] = val
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

    def change_slider(self, dec, large):
        """Change the value of the currently focused slider.

        Args:
            dec: If True decrease the value.
            large: If True use large step (10) instead of small one (1)
        """
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            if scale.is_focus():
                val = scale.get_value()
                if self.vimiv.keyhandler.num_str:
                    step = int(self.vimiv.keyhandler.num_str)
                    self.vimiv.keyhandler.num_str = ""
                elif large:
                    step = 10
                else:
                    step = 1
                if dec:
                    val -= step
                else:
                    val += step
                scale.set_value(val)

    def button_clicked(self, button, accept=False):
        """Finish manipulate mode.

        Args:
            button: Gtk.Button that was clicked.
            accept: If True apply changes to image file. Else discard them.
        """
        # Reload the real images if changes were made
        if "EDIT" in self.vimiv.paths[self.vimiv.index]:
            # manipulated thumbnail
            out = self.vimiv.paths[self.vimiv.index]
            orig = out.replace("EDIT", "EDIT-ORIG")  # original thumbnail
            path = out.replace("-EDIT", "")          # real file
            # Edit the actual file if yes
            if accept:
                self.manipulate_image(path)
            # Reset all the manipulations
            self.manipulations = [1, 1, 1, False]
            for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
                scale.set_value(0)
            # Remove the thumbnail files used
            os.remove(out)
            os.remove(orig)
            # Show the original image
            self.vimiv.image.pixbuf_original = \
                GdkPixbuf.PixbufAnimation.new_from_file(path)
            self.vimiv.image.pixbuf_original = \
                self.vimiv.image.pixbuf_original.get_static_image()
            self.vimiv.paths[self.vimiv.index] = path
            if not self.vimiv.window.fullscreen:
                self.vimiv.image.imsize = self.vimiv.image.get_available_size()
            self.vimiv.image.zoom_percent = self.vimiv.image.get_zoom_percent()
            self.vimiv.image.update()
        # Done
        self.toggle()
        self.vimiv.statusbar.update_info()

    def button_opt_clicked(self, button):
        """Set optimize to True and run the manipulation.

        Args:
            button: Gtk.Button that was clicked.
        """
        self.manipulations[3] = True
        self.manipulate_image()

    def cmd_edit(self, manipulation, num="0"):
        """Run the specified manipulation.

        Args:
            manipulation: Name of manipulation to run.
            num: Value for setting the slider.
        """
        if not self.toggled:
            if not self.vimiv.paths:
                self.vimiv.statusbar.err_message("No image to manipulate")
                return
            else:
                self.toggle()
        if manipulation == "opt":
            self.button_opt_clicked("button_widget")
        else:
            self.focus_slider(manipulation)
            self.vimiv.keyhandler.num_str = num
            execstr = "self.scale_" + manipulation + \
                ".set_value(int(self.vimiv.keyhandler.num_str))"
            exec(execstr)
        self.vimiv.keyhandler.num_str = ""
