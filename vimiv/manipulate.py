# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Manipulate part for vimiv."""

import os
from threading import Thread

from gi.repository import GdkPixbuf, GLib, Gtk
from PIL import Image, ImageEnhance
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
        sliders: Dictionary containing bri, con and sha sliders.
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
        self.simple_manipulations = {}
        self.manipulations = {"bri": 1, "con": 1, "sha": 1}
        self.pil_image = Image
        self.pil_thumb = Image

        # A scrollable window so all tools are always accessible
        self.scrolled_win = Gtk.ScrolledWindow()
        # A grid in which everything gets packed
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_border_width(6)
        grid.connect("key_press_event", self.app["eventhandler"].run,
                     "MANIPULATE")
        self.scrolled_win.add(grid)

        # sliders
        bri_slider = Gtk.Scale()
        bri_slider.connect("value-changed", self.value_slider, "bri")
        con_slider = Gtk.Scale()
        con_slider.connect("value-changed", self.value_slider, "con")
        sha_slider = Gtk.Scale()
        sha_slider.connect("value-changed", self.value_slider, "sha")
        self.sliders = {"bri": bri_slider, "con": con_slider, "sha": sha_slider}

        # Set some properties
        for slider in self.sliders.values():
            slider.set_range(-127, 127)
            slider.set_size_request(120, 20)
            slider.set_value(0)
            slider.set_digits(0)

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
        for item in [bri_label, bri_slider, con_label, con_slider,
                     sha_label, sha_slider, separator, button_yes,
                     button_no]:
            grid.add(item)

    def delete(self):
        """Delete all marked images or the current one."""
        # Get all images
        images = self.get_manipulated_images("Deleted")
        self.app["mark"].marked = []
        # Delete all images
        for im in images:
            message = ""
            if not os.path.exists(im):
                message = "Image %s does not exist" % (im)
            elif os.path.isdir(im):
                message = "Deleting directories is not supported"
            if message:
                self.app["statusbar"].message(message, "error")
                return
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
                self.app["statusbar"].message("No more images", "info")

    def get_manipulated_images(self, info):
        """Return the images which should be manipulated.

        Either the currently focused image or all marked images.

        Args:
            info: Info to display when acting on marked images.
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
            if len(images) == 1:
                message = "%s %d marked image" % (info, len(images))
            else:
                message = "%s %d marked images" % (info, len(images))
            self.app["statusbar"].message(message, "info")
        # Delete all thumbnails of manipulated images
        thumbnails = os.listdir(self.app["thumbnail"].directory)
        thumbnail_class = imageactions.Thumbnails(
            images, self.app["thumbnail"].sizes[-1],
            self.app["thumbnail"].directory)
        for im in images:
            thumb = thumbnail_class.create_thumbnail_name(im)
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
        # Do not rotate animations
        if self.app["image"].is_anim:
            self.app["statusbar"].message(
                "Animations cannot be rotated", "warning")
            return
        elif not self.app.paths:
            self.app["statusbar"].message(
                "No image to rotate", "error")
            return
        try:
            cwise = int(cwise)
            images = self.get_manipulated_images("Rotated")
            cwise = cwise % 4
            # Rotate the image shown
            if self.app.paths[self.app.index] in images:
                self.app["image"].pixbuf_original = \
                    self.app["image"].pixbuf_original.rotate_simple(
                        (90 * cwise))
                if self.app["image"].fit_image:
                    self.app["image"].zoom_percent = \
                        self.app["image"].get_zoom_percent_to_fit(
                            self.app["image"].fit_image)
                self.app["image"].update(False, False)
            if rotate_file:
                for fil in images:
                    if fil in self.simple_manipulations:
                        self.simple_manipulations[fil][0] = \
                            (self.simple_manipulations[fil][0] + cwise) % 4
                    else:
                        self.simple_manipulations[fil] = [cwise, 0, 0]
                # Reload thumbnails of rotated images immediately
                if self.app["thumbnail"].toggled:
                    self.run_simple_manipulations()
        except ValueError:
            self.app["statusbar"].message(
                "Argument for rotate must be of type integer", "error")

    def run_simple_manipulations(self):
        """Start thread for rotate and flip."""
        t = Thread(target=self.thread_for_simple_manipulations)
        t.start()

    def thread_for_simple_manipulations(self):
        """Rotate and flip image file in an extra thread."""
        to_remove = list(self.simple_manipulations.keys())
        for f in self.simple_manipulations:
            if self.simple_manipulations[f][0]:
                imageactions.rotate_file([f],
                                         self.simple_manipulations[f][0])
            if self.simple_manipulations[f][1]:
                imageactions.flip_file([f], True)
            if self.simple_manipulations[f][2]:
                imageactions.flip_file([f], False)
            if self.app["thumbnail"].toggled:
                self.app["thumbnail"].reload(f)
        for key in to_remove:
            del self.simple_manipulations[key]

    def flip(self, horizontal, flip_file=True):
        """Flip the displayed image and call thread to flip files.

        Args:
            horizontal: If 1 flip horizontally. Else vertically.
            rotate_file: If True call thread to rotate files.
        """
        # Do not flip animations
        if self.app["image"].is_anim:
            self.app["statusbar"].message(
                "Animations cannot be flipped", "warning")
            return
        elif not self.app.paths:
            self.app["statusbar"].message(
                "No image to flip", "error")
            return
        try:
            horizontal = int(horizontal)
            images = self.get_manipulated_images("Flipped")
            # Flip the image shown
            if self.app.paths[self.app.index] in images:
                self.app["image"].pixbuf_original = \
                    self.app["image"].pixbuf_original.flip(horizontal)
                self.app["image"].update(False)
            if flip_file:
                for fil in images:
                    if fil not in self.simple_manipulations:
                        self.simple_manipulations[fil] = [0, 0, 0]
                    if horizontal:
                        self.simple_manipulations[fil][1] = \
                            (self.simple_manipulations[fil][1] + 1) % 2
                    else:
                        self.simple_manipulations[fil][2] = \
                            (self.simple_manipulations[fil][2] + 1) % 2
                # Reload thumbnails of flipped images immediately
                if self.app["thumbnail"].toggled:
                    self.run_simple_manipulations()
        except ValueError:
            self.app["statusbar"].message(
                "Argument for flip must be of type integer", "error")

    def rotate_auto(self):
        """Autorotate all pictures in the current pathlist."""
        amount, method = imageactions.autorotate(self.app.paths)
        if amount:
            self.app["image"].load_image()
            message = "Autorotated %d image(s) using %s." % (amount, method)
        else:
            message = "No image rotated. Tried using %s." % (method)
        self.app["statusbar"].message(message, "info")

    def toggle(self):
        """Toggle the manipulation bar."""
        if self.scrolled_win.is_visible():
            self.scrolled_win.hide()
            self.app["image"].scrolled_win.grab_focus()
            self.app["statusbar"].update_info()
        elif self.app.paths and not(self.app["thumbnail"].toggled or
                                    self.app["library"].treeview.is_focus()):
            if os.path.islink(self.app.paths[self.app.index]):
                self.app["statusbar"].message(
                    "Manipulating symbolic links is not supported", "warning")
            elif self.app["image"].is_anim:
                self.app["statusbar"].message(
                    "Manipulating Gifs is not supported", "warning")
            else:
                self.scrolled_win.show()
                self.sliders["bri"].grab_focus()
                self.app["statusbar"].update_info()
                # Create PIL image to work with
                size = self.app["image"].imsize
                self.pil_image = Image.open(self.app.paths[self.app.index])
                self.pil_thumb = Image.open(self.app.paths[self.app.index])
                # pylint: disable=no-member
                self.pil_thumb.thumbnail(size, Image.ANTIALIAS)
        else:
            if self.app["thumbnail"].toggled:
                self.app["statusbar"].message(
                    "Manipulate not supported in thumbnail mode", "warning")
            elif self.app["library"].treeview.is_focus():
                self.app["statusbar"].message(
                    "Manipulate not supported in library", "warning")
            else:
                self.app["statusbar"].message("No image open to edit",
                                              "warning")

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
        # If manipulate is not toggled, this makes no sense
        if not self.scrolled_win.is_visible():
            self.app["statusbar"].message(
                "Focusing a slider only makes sense in manipulate", "error")
        elif name not in self.sliders:
            self.app["statusbar"].message(
                "No slider called " + name, "error")
        else:
            self.sliders[name].grab_focus()

    def change_slider(self, step=1):
        """Change the value of the currently focused slider.

        Args:
            step: Step to edit the slider by.
        """
        try:
            step = int(step)
        except ValueError:
            self.app["statusbar"].message(
                "Argument for slider must be of type integer", "error")
            return
        for slider in self.sliders.values():
            if slider.is_focus():
                val = slider.get_value()
                step = self.app["eventhandler"].num_receive() * step
                val += step
                slider.set_value(val)

    def button_clicked(self, button, accept=False):
        """Finish manipulate mode.

        Args:
            button: Gtk.Button that was clicked.
            accept: If True apply changes to image file. Else discard them.
        """
        # If manipulate is not toggled, this makes no sense
        if not self.scrolled_win.is_visible():
            self.app["statusbar"].message(
                "Finishing manipulate only makes sense in manipulate", "error")
            return
        # Apply changes
        if accept:
            self.manipulate_image(True)
        # Reset all the manipulations
        self.manipulations = {"bri": 1, "con": 1, "sha": 1}
        for slider in self.sliders.values():
            slider.set_value(0)
        # Show the original image
        self.app["image"].fit_image = 1
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
        # Catch buggy numbers
        if not num.isdigit():
            self.app["statusbar"].message(
                "Argument must be of type integer", "error")
            return
        if not self.scrolled_win.is_visible():
            if not self.app.paths:
                self.app["statusbar"].message("No image to manipulate", "error")
                return
            else:
                self.toggle()
        self.focus_slider(manipulation)
        self.sliders[manipulation].set_value(int(num))
