# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Manipulate part for vimiv."""

import os

from gi.repository import Gtk, GdkPixbuf
from vimiv import image_enhance
from vimiv.fileactions import is_animation
from vimiv.imageactions import save_pixbuf


class Manipulate(Gtk.ScrolledWindow):
    """Manipulate class for vimiv.

    Includes the manipulation toolbar and all the actions that apply to it.

    Attributes:
        sliders: Dictionary containing bri, con and sat sliders.

        _app: The main vimiv application to interact with.
        _manipulations: Dictionary of possible manipulations. Includes
            brightness, contrast and saturation.
        _pixbuf: Shrinked GdkPixbuf.Pixbuf to work on. Received from Image on
            entry.
        _pixbuf_original: Original GdkPixbuf.Pixbuf to write to file if
            manipulations are accepted. Received from Image on entry.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(Manipulate, self).__init__()
        self._app = app

        # Defaults
        self._manipulations = {"bri": 1, "con": 1, "sat": 1}
        self._pixbuf = GdkPixbuf.Pixbuf()
        self._pixbuf_original = GdkPixbuf.Pixbuf()

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
        sat_slider = Gtk.Scale()
        sat_slider.connect("value-changed", self._set_slider_value, "sat")
        self.sliders = {"bri": bri_slider, "con": con_slider, "sat": sat_slider}

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
        sat_label = Gtk.Label()
        sat_label.set_markup("\n<b>Sat</b>")

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
                     sat_label, sat_slider, separator, button_yes,
                     button_no]:
            grid.add(item)

    def check_for_edit(self, force):
        """Check if an image was edited.

        Args:
            force: If True move and ignore any editing.
        Return:
            0 if no edits were done or force, 1 else.
        """
        if force:
            self._manipulations = {"bri": 1, "con": 1, "sat": 1}
            return 0
        elif self._manipulations != {"bri": 1, "con": 1, "sat": 1}:
            self._app["statusbar"].message(
                "Image has been edited, add ! to force", "warning")
            return 1
        return 0

    def toggle(self):
        """Toggle the manipulation bar."""
        if self.is_visible():
            self.hide()
            self._app["main_window"].grab_focus()
            self._app["statusbar"].update_info()
        elif self._app.get_paths() and \
                self._app.get_focused_widget() not in ["lib", "thu"]:
            if os.path.islink(self._app.get_path()):
                self._app["statusbar"].message(
                    "Manipulating symbolic links is not supported", "warning")
            elif is_animation(self._app.get_path()):
                self._app["statusbar"].message(
                    "Manipulating Gifs is not supported", "warning")
            else:
                self.show()
                self._pixbuf = self._app["image"].get_pixbuf()
                self._pixbuf_original = self._app["image"].get_pixbuf_original()
                self.sliders["bri"].grab_focus()
                self._app["statusbar"].update_info()
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

    def _apply(self, real=False):
        """Apply manipulations to image.

        Manipulations are the three sliders for brightness, contrast and
        saturation. They are applied to a thumbnail by default and can act on the
        real image.

        Args:
            real: If True, apply manipulations to the real image and save it.
        """
        pixbuf = self._pixbuf_original if real else self._pixbuf.copy()
        # Apply brightness, contrast and saturation
        pixbuf = image_enhance.enhance_bc(pixbuf, self._manipulations["bri"],
                                          self._manipulations["con"])
        pixbuf.saturate_and_pixelate(pixbuf, self._manipulations["sat"], False)
        # Show the edited pixbuf
        self._app["image"].set_pixbuf(pixbuf)
        self._app["image"].zoom_to(0)
        # Save file if needed
        if real:
            save_pixbuf(pixbuf, self._app.get_path())

    def _set_slider_value(self, slider, name):
        """Set value of self._manipulations according to slider value.

        Args:
            slider: Gtk.Scale on which to operate.
            name: Name of slider to operate on.
        """
        val = slider.get_value()
        val = (val + 127) / 127
        # Change brightness, contrast or saturation
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
            self._apply(real=True)
        # Reset all the manipulations
        self._manipulations = {"bri": 1, "con": 1, "sat": 1}
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
            if not self._app.get_paths():
                self._app["statusbar"].message(
                    "No image to manipulate", "error")
                return
            else:
                self.toggle()
        self.focus_slider(manipulation)
        self.sliders[manipulation].set_value(int(num))
