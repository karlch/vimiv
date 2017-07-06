# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Provides a class to manage settings and methods dealing with conversion."""

import os

from gi.repository import GLib


class WrongSettingValue(Exception):
    """Raised when a setting does not have the correct format."""

class SettingNotFoundError(Exception):
    """Raised when a setting does not exist."""


class Setting(object):
    """Stores a setting and its attributes.

    By default the setting is of type boolean.

    Attributes:
        name: Name of the setting as string.

        _datatype: Python type of the setting.
        _default_value: Default value of the setting stored in its python type.
        _value: Value of the setting stored in its python type.
    """

    def __init__(self, name, default_value):
        """Initialize attributes with default values.

        Args:
            name: Name of the setting to initialize.
            default_value: Default value of the setting to start with.
        """
        self.name = name
        self._default_value = default_value
        self._value = default_value
        self._n = 0

    def get_default(self):
        return self._default_value

    def get_value(self):
        return self._value

    def is_default(self):
        return self._value == self._default_value

    def set_to_default(self):
        self._value = self._default_value

    def override(self, new_value):
        """Override the setting with a new boolean value.

        This is the default and gets overriden by other setting classes.

        Args:
            new_value: String to convert to a boolean for the new value.
        """
        self._value = get_boolean(new_value)


class IntSetting(Setting):
    """Stores an integer setting."""

    def override(self, new_value):
        self._value = get_int(new_value)


class FloatSetting(Setting):
    """Stores a float setting."""

    def override(self, new_value):
        self._value = get_float(new_value)


class ThumbnailSizeSetting(Setting):
    """Stores a thumbnail size setting.

    This setting is stored as a python tuple with two equal integer values. The
    integer value must be one of 64, 128, 256, 512.
    """

    def override(self, new_value):
        """Override the setting with a new thumbnail size.

        Args:
            new_value: String in the form of "(val, val)" for the new value.
        """
        new_value = new_value.lstrip("(").rstrip(")")
        int_tuple = new_value.split(",")
        if len(int_tuple) != 2:
            error = "Tuple must be of the form (val, val)."
            raise WrongSettingValue(error)
        int_tuple = (get_int(int_tuple[0]), get_int(int_tuple[1]))
        if int_tuple[0] != int_tuple[1]:
            error = "Thumbnail width and height must be equal"
            raise WrongSettingValue(error)
        if int_tuple[0] not in [64, 128, 256, 512]:
            error = "Thumbnail size must be one of 64, 128, 256 and 512."
            raise WrongSettingValue(error)
        self._value = tuple(int_tuple)


class GeometrySetting(Setting):
    """Stores a geometry setting.

    This setting is stored as python tuple of the form (width, height) and can
    be set from a string in the form "WIDTHxHEIGHT".
    """

    def override(self, new_value):
        """Override the setting with a new geometry.

        Args:
            new_value: String in the form of "WIDTHxHEIGHT" for the new value.
        """
        geometry = new_value.split("x")
        if len(geometry) != 2:
            error = "Geometry must be of the form WIDTHxHEIGHT."
            raise WrongSettingValue(error)
        self._value = (get_int(geometry[0]), get_int(geometry[1]))


class DirectorySetting(Setting):
    """Stores a directory setting.

    This setting gets stored as a python string containing the absolute path of
    the directory. Override checks if the directory exists.
    """

    def override(self, new_value):
        directory = os.path.abspath(os.path.expanduser(new_value))
        if os.path.isdir(directory):
            self._value = directory
        else:
            error = "Directory %s does not exist." % (new_value)
            raise WrongSettingValue(error)


class MarkupSetting(Setting):
    """Stores a markup setting to highlight e.g. search results.

    This setting gets stored as a python string but it must be closeable via
    "</span>". The valid default is '<span foreground="#875FFF">'.
    """

    def override(self, new_value):
        new_value = new_value.strip()
        if not new_value.startswith("<span"):
            error = 'Markup must start with "<span"'
            raise WrongSettingValue(error)
        elif not new_value.endswith(">"):
            error = 'Markup must end with ">"'
            raise WrongSettingValue(error)
        self._value = GLib.markup_escape_text(new_value)

class SettingStorage(object):
    """Stores all settings for vimiv.

    Settings can be accessed via SettingStorage["setting_name"] and changed by
    calling SettingStorage.override("setting_name", new_value).

    Attributes:
        _settings: List of all Setting objects. Should not be accessed directly.
        _n: Integer for iterator.
    """

    def __init__(self):
        self._settings = [
            Setting("start_fullscreen", False),
            Setting("start_slideshow", False),
            FloatSetting("slideshow_delay", 2.0),
            Setting("shuffle", False),
            Setting("display_bar", True),
            ThumbnailSizeSetting("default_thumbsize", (128, 128)),
            GeometrySetting("geometry", (800, 600)),
            Setting("search_case_sensitive", True),
            Setting("incsearch", True),
            Setting("recursive", False),
            Setting("rescale_svg", True),
            FloatSetting("overzoom", 1.0),
            Setting("copy_to_primary", False),
            IntSetting("commandline_padding", 6),
            IntSetting("thumb_padding", 10),
            IntSetting("completion_height", 200),
            Setting("autoplay_gifs", True),
            Setting("show_library", False),
            IntSetting("library_width", 300),
            Setting("expand_lib", True),
            IntSetting("border_width", 0),
            MarkupSetting("markup", '<span foreground="#875FFF">'),
            Setting("show_hidden", False),
            DirectorySetting("desktop_start_dir", os.path.expanduser("~")),
            IntSetting("file_check_amount", 30),
            Setting("tilde_in_statusbar", True)]
        self._n = 0

    def override(self, name, new_value):
        """Override a setting in the storage.

        Args:
            name: Name of the setting to override.
            new_value: Value to override the setting with.
        """
        setting = self[name]
        setting.override(new_value)

    def reset(self):
        """Reset all settings to their default value."""
        for setting in self:
            setting.set_to_default()

    def __getitem__(self, name):
        """Receive a setting via its name."""
        for setting in self._settings:
            if setting.name == name:
                return setting
        raise SettingNotFoundError("No setting called %s." % (name))

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        """Iterate over settings."""
        if (self._n - 1) < len(self._settings) - 1:
            self._n += 1
            return self._settings[self._n  - 1]
        else:
            raise StopIteration


def get_boolean(value):
    """Convert a value to a boolean.

    Args:
        value: String value to convert.
    Return:
        bool: True if string.lower() in ["yes", "true"]. False otherwise.
    """
    return True if value.lower() in ["yes", "true"] else False


def get_int(value):
    """Convert a value to a positive integer.

    Args:
        value: String value to convert.
    Return:
        int(value) if possible.
    """
    try:
        int_val = int(value)
    except ValueError:
        error = "Could not convert %s to int." % (value)
        raise WrongSettingValue(error)
    if int_val < 0:
        raise WrongSettingValue("Negative numbers are not supported.")
    return int_val


def get_float(value):
    """Convert a value to a positive float.

    Args:
        value: String value to convert.
    Return:
        float(value) if possible.
    """
    try:
        float_val = float(value)
    except ValueError:
        error = "Could not convert %s to float." % (value)
        raise WrongSettingValue(error)
    if float_val < 0:
        raise WrongSettingValue("Negative numbers are not supported.")
    return float_val


# Initialize an actual SettingsStorage object to work with
settings = SettingStorage()
