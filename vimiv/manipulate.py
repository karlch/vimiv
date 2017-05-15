# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Manipulate part for vimiv."""

import os
from threading import Thread

from gi.repository import GdkPixbuf, GLib, Gtk
from PIL import Image, ImageEnhance
from vimiv import imageactions
from vimiv.trash_manager import TrashManager
from vimiv.fileactions import is_animation


class Manipulate(Gtk.ScrolledWindow):
    """Manipulate class for vimiv.

    Includes the manipulation toolbar, all the actions that apply to it and all
    the other image manipulations like rotate, flip, and so on.

    Attributes:
        sliders: Dictionary containing bri, con and sha sliders.
        trash_manager: Class to handle a shared trash directory.

        _app: The main vimiv application to interact with.
        _manipulations: Dictionary of possible manipulations. Includes
            brightness, contrast and sharpness.
        _pil_image: PIL Image of the original size for accepted manipulations.
        _pil_thumb: Thumbnail of PIL image to work on temporarily.
        _simple_manipulations: Dictionary for rotate and flip.
            Key: Filename; Item: [Int, Bool, Bool]
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(Manipulate, self).__init__()
        self._app = app

        # Settings
        self._simple_manipulations = {}
        self._manipulations = {"bri": 1, "con": 1, "sha": 1}
        self._pil_image = Image
        self._pil_thumb = Image

        # A scrollable window so all tools are always accessible
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        # A grid in which everything gets packed
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_border_width(6)
        grid.connect("key_press_event", self._app["eventhandler"].on_key_press,
                     "MANIPULATE")
        self.add(grid)

        # Sliders
        bri_slider = Gtk.Scale()
        bri_slider.connect("value-changed", self._set_slider_value, "bri")
        con_slider = Gtk.Scale()
        con_slider.connect("value-changed", self._set_slider_value, "con")
        sha_slider = Gtk.Scale()
        sha_slider.connect("value-changed", self._set_slider_value, "sha")
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
        button_yes.connect("clicked", self._on_button_clicked, True)
        button_yes.set_size_request(80, 20)
        button_no = Gtk.Button(label="Cancel")
        button_no.connect("clicked", self._on_button_clicked, False)
        button_no.set_size_request(80, 20)

        # Pack everything into the grid
        for item in [bri_label, bri_slider, con_label, con_slider,
                     sha_label, sha_slider, separator, button_yes,
                     button_no]:
            grid.add(item)

        # Generate trash manager
        self.trash_manager = TrashManager()

    def check_for_edit(self, force):
        """Check if an image was edited.

        Args:
            force: If True move and ignore any editing.
        Return:
            0 if no edits were done or force, 1 else.
        """
        if force:
            self._manipulations = {"bri": 1, "con": 1, "sha": 1}
            return 0
        elif self._manipulations != {"bri": 1, "con": 1, "sha": 1}:
            self._app["statusbar"].message(
                "Image has been edited, add ! to force", "warning")
            return 1
        return 0

    def delete(self):
        """Delete all marked images or the current one."""
        # Get all images
        images = self.get_manipulated_images("Deleted")
        self._app["mark"].marked = []
        # Delete all images remembering possible errors
        message = ""
        for im in images:
            if not os.path.exists(im):
                message += "Image %s does not exist." % (im)
            elif os.path.isdir(im):
                message += "Deleting directory %s is not supported." % (im)
            else:
                self.trash_manager.delete(im)
        if message:
            self._app["statusbar"].message(message, "error")

        self._app.emit("paths-changed", self)

    def undelete(self, basename):
        """Undelete an image in the trash.

        Args:
            basename: The basename of the image in the trash directory.
        """
        returncode = self.trash_manager.undelete(basename)
        if returncode == 1:
            message = "Could not restore %s, file does not exist" % (basename)
            self._app["statusbar"].message(message, "error")
        elif returncode == 2:
            message = "Could not restore %s, directories are not supported" \
                % (basename)
            self._app["statusbar"].message(message, "error")
        elif returncode == 3:
            message = "Could not restore %s, directory is not accessible" \
                % (basename)
            self._app["statusbar"].message(message, "error")
        else:
            self._app.emit("paths-changed", self)

    def get_manipulated_images(self, info):
        """Return the images which should be manipulated.

        Either the currently focused image or all marked images.

        Args:
            info: Info to display when acting on marked images.
        """
        images = []
        # Add the image shown
        if not self._app["mark"].marked and not self._app["thumbnail"].toggled:
            if self._app["library"].is_focus():
                images.append(
                    os.path.abspath(self._app.get_pos(True)))
            else:
                images.append(self._app.paths[self._app.index])
        # Add all marked images
        else:
            images = self._app["mark"].marked
            if len(images) == 1:
                message = "%s %d marked image" % (info, len(images))
            else:
                message = "%s %d marked images" % (info, len(images))
            self._app["statusbar"].message(message, "info")
        return images

    def rotate(self, cwise, rotate_file=True):
        """Rotate the displayed image and call thread to rotate files.

        Args:
            cwise: Rotate image 90 * cwise degrees.
            rotate_file: If True call thread to rotate files.
        """
        if not self._app.paths:
            self._app["statusbar"].message(
                "No image to rotate", "error")
            return
        # Do not rotate animations
        elif is_animation(self._app.paths[self._app.index]):
            self._app["statusbar"].message(
                "Animations cannot be rotated", "warning")
            return
        try:
            cwise = int(cwise)
            images = self.get_manipulated_images("Rotated")
            cwise = cwise % 4
            # Rotate the image shown
            if self._app.paths[self._app.index] in images:
                self._app["image"].pixbuf_original = \
                    self._app["image"].pixbuf_original.rotate_simple(
                        (90 * cwise))
                if self._app["image"].fit_image:
                    self._app["image"].zoom_to(0, self._app["image"].fit_image)
            if rotate_file:
                for fil in images:
                    if fil in self._simple_manipulations:
                        self._simple_manipulations[fil][0] = \
                            (self._simple_manipulations[fil][0] + cwise) % 4
                    else:
                        self._simple_manipulations[fil] = [cwise, 0, 0]
                # Reload thumbnails of rotated images immediately
                if self._app["thumbnail"].toggled:
                    self.run_simple_manipulations()
        except ValueError:
            self._app["statusbar"].message(
                "Argument for rotate must be of type integer", "error")

    def run_simple_manipulations(self):
        """Start thread for rotate and flip."""
        t = Thread(target=self._thread_for_simple_manipulations)
        t.start()

    def _thread_for_simple_manipulations(self):
        """Rotate and flip image file in an extra thread."""
        to_remove = list(self._simple_manipulations.keys())
        for f in self._simple_manipulations:
            if self._simple_manipulations[f][0]:
                imageactions.rotate_file([f],
                                         self._simple_manipulations[f][0])
            if self._simple_manipulations[f][1]:
                imageactions.flip_file([f], True)
            if self._simple_manipulations[f][2]:
                imageactions.flip_file([f], False)
            if self._app["thumbnail"].toggled:
                self._app["thumbnail"].reload(f)
        for key in to_remove:
            del self._simple_manipulations[key]

    def flip(self, horizontal, flip_file=True):
        """Flip the displayed image and call thread to flip files.

        Args:
            horizontal: If 1 flip horizontally. Else vertically.
            rotate_file: If True call thread to rotate files.
        """
        if not self._app.paths:
            self._app["statusbar"].message(
                "No image to flip", "error")
            return
        # Do not flip animations
        elif is_animation(self._app.paths[self._app.index]):
            self._app["statusbar"].message(
                "Animations cannot be flipped", "warning")
            return
        try:
            horizontal = int(horizontal)
            images = self.get_manipulated_images("Flipped")
            # Flip the image shown
            if self._app.paths[self._app.index] in images:
                self._app["image"].pixbuf_original = \
                    self._app["image"].pixbuf_original.flip(horizontal)
                self._app["image"].update(False)
            if flip_file:
                for fil in images:
                    if fil not in self._simple_manipulations:
                        self._simple_manipulations[fil] = [0, 0, 0]
                    if horizontal:
                        self._simple_manipulations[fil][1] = \
                            (self._simple_manipulations[fil][1] + 1) % 2
                    else:
                        self._simple_manipulations[fil][2] = \
                            (self._simple_manipulations[fil][2] + 1) % 2
                # Reload thumbnails of flipped images immediately
                if self._app["thumbnail"].toggled:
                    self.run_simple_manipulations()
        except ValueError:
            self._app["statusbar"].message(
                "Argument for flip must be of type integer", "error")

    def rotate_auto(self):
        """Autorotate all pictures in the current pathlist."""
        amount, method = imageactions.autorotate(self._app.paths)
        if amount:
            self._app["image"].load()
            message = "Autorotated %d image(s) using %s." % (amount, method)
        else:
            message = "No image rotated. Tried using %s." % (method)
        self._app["statusbar"].message(message, "info")

    def toggle(self):
        """Toggle the manipulation bar."""
        if self.is_visible():
            self.hide()
            self._app["main_window"].grab_focus()
            self._app["statusbar"].update_info()
        elif self._app.paths and not(self._app["thumbnail"].toggled or
                                     self._app["library"].is_focus()):
            if os.path.islink(self._app.paths[self._app.index]):
                self._app["statusbar"].message(
                    "Manipulating symbolic links is not supported", "warning")
            elif is_animation(self._app.paths[self._app.index]):
                self._app["statusbar"].message(
                    "Manipulating Gifs is not supported", "warning")
            else:
                self.show()
                self.sliders["bri"].grab_focus()
                self._app["statusbar"].update_info()
                # Create PIL image to work with
                size = self._app["image"].get_allocated_size()[0]
                size = (size.width, size.height)
                self._pil_image = Image.open(self._app.paths[self._app.index])
                self._pil_thumb = Image.open(self._app.paths[self._app.index])
                self._pil_thumb.thumbnail(size, Image.ANTIALIAS)
        else:
            if self._app["thumbnail"].toggled:
                self._app["statusbar"].message(
                    "Manipulate not supported in thumbnail mode", "warning")
            elif self._app["library"].is_focus():
                self._app["statusbar"].message(
                    "Manipulate not supported in library", "warning")
            else:
                self._app["statusbar"].message("No image open to edit",
                                               "warning")

    def _apply(self, apply_to_file=False):
        """Apply manipulations to image.

        Manipulations are the three sliders for brightness, contrast and
        sharpness. They are applied to a thumbnail by default and can act on the
        real image.

        Args:
            real: If True, apply manipulations to the real image.
        """
        if apply_to_file:
            imfile = self._pil_image
        else:
            imfile = self._pil_thumb
        # Apply Brightness, Contrast and Sharpness
        enhanced_im = ImageEnhance.Brightness(imfile).enhance(
            self._manipulations["bri"])
        enhanced_im = ImageEnhance.Contrast(enhanced_im).enhance(
            self._manipulations["con"])
        enhanced_im = ImageEnhance.Sharpness(enhanced_im).enhance(
            self._manipulations["sha"])
        # On real file save data to file
        if apply_to_file:
            imageactions.save_image(enhanced_im,
                                    self._app.paths[self._app.index])
        # Load Pixbuf from PIL data
        data = enhanced_im.tobytes()
        g_data = GLib.Bytes.new(data)
        w, h = imfile.size
        if imfile.mode == "RGBA":
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                g_data, GdkPixbuf.Colorspace.RGB, True, 8, w, h, 4 * w)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                g_data, GdkPixbuf.Colorspace.RGB, False, 8, w, h, 3 * w)
        # Show the edited pixbuf
        self._app["image"].pixbuf_original = pixbuf
        self._app["image"].update()
        self._app["image"].zoom_to(0)

    def _set_slider_value(self, slider, name):
        """Set value of self._manipulations according to slider value.

        Args:
            slider: Gtk.Scale on which to operate.
            name: Name of slider to operate on.
        """
        val = slider.get_value()
        val = (val + 127) / 127
        # Change brightness, contrast or sharpness
        self._manipulations[name] = val
        # Run the manipulation function
        self._apply()

    def focus_slider(self, name):
        """Set focus on one of the three sliders.

        Args:
            name: Name of slider to focus.
        """
        # If manipulate is not toggled, this makes no sense
        if not self.is_visible():
            self._app["statusbar"].message(
                "Focusing a slider only makes sense in manipulate", "error")
        elif name not in self.sliders:
            self._app["statusbar"].message(
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
            self._app["statusbar"].message(
                "Argument for slider must be of type integer", "error")
            return
        for slider in self.sliders.values():
            if slider.is_focus():
                val = slider.get_value()
                step = self._app["eventhandler"].num_receive() * step
                val += step
                slider.set_value(val)

    def _on_button_clicked(self, button, accept=False):
        self.finish(accept)

    def finish(self, accept=False):
        """Finish manipulate mode.

        Args:
            accept: If True apply changes to image file. Else discard them.
        """
        # If manipulate is not toggled, this makes no sense
        if not self.is_visible():
            self._app["statusbar"].message(
                "Finishing manipulate only makes sense in manipulate", "error")
            return
        # Apply changes
        if accept:
            self._apply(True)
        # Reset all the manipulations
        self._manipulations = {"bri": 1, "con": 1, "sha": 1}
        for slider in self.sliders.values():
            slider.set_value(0)
        # Show the original image
        self._app["image"].fit_image = 1
        self._app["image"].load()
        # Done
        self.toggle()

    def cmd_edit(self, manipulation, num="0"):
        """Run the specified manipulation.

        Args:
            manipulation: Name of manipulation to run.
            num: Value for setting the slider.
        """
        # Catch buggy numbers
        if not num.isdigit():
            self._app["statusbar"].message(
                "Argument must be of type integer", "error")
            return
        if not self.is_visible():
            if not self._app.paths:
                self._app["statusbar"].message(
                    "No image to manipulate", "error")
                return
            else:
                self.toggle()
        self.focus_slider(manipulation)
        self.sliders[manipulation].set_value(int(num))

    def threads_running(self):
        """Return True or False depending on whether threads are running."""
        return True if self._simple_manipulations.keys() else False
