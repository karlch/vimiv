#!/usr/bin/env python3
# encoding: utf-8
"""All parsers for vimiv."""
import configparser
import os
import sys
from vimiv.helpers import error_message


def set_defaults():
    """Return the default settings for vimiv.

    Return: Dictionary of default settings.
    """
    general = {"start_fullscreen": False,
               "start_slideshow": False,
               "slideshow_delay": 2,
               "shuffle": False,
               "display_bar": True,
               "thumbsize": (128, 128),
               "thumb_maxsize": (256, 256),
               "geometry": (800, 600),
               "search_case_sensitive": True,
               "incsearch": True,
               "recursive": False,
               "rescale_svg": True,
               "overzoom": False,
               "cache_thumbnails": True,
               "copy_to_primary": False,
               "commandline_padding": 6,
               "completion_height": 200}
    library = {"show_library": False,
               "library_width": 300,
               "expand_lib": True,
               "border_width": 0,
               "markup": '<span foreground="#875FFF">',
               "show_hidden": False,
               "desktop_start_dir": os.path.expanduser("~"),
               "file_check_amount": 30}
    aliases = {}
    settings = {"GENERAL": general, "LIBRARY": library, "ALIASES": aliases}
    return settings


def overwrite_section(key, config, settings):
    """Overwrite a section in settings with the settings in a configfile.

    Args:
        key: One of "GENERAL" or "LIBRARY" indicating the main section.
        config: configparser.ConfigParser of the configfile.
        settings: Dictionary of settings to operate on.

    Return:
        settings: Dictionary of modified settings.
        message: Error message for settings that are given in an invalid way.
    """
    section = config[key]
    message = ""
    for setting in section.keys():
        if setting not in settings[key]:
            message += "Ignoring unknown setting %s." % (setting)
            continue
        # Parse the setting so it gets the correct value
        try:
            if setting == "geometry":
                file_set = (int(section[setting].split("x")[0]),
                            int(section[setting].split("x")[1]))
            elif setting in ["thumbsize", "thumb_maxsize"]:
                file_set = section[setting].lstrip("(").rstrip(")")
                file_set = file_set.split(",")
                file_set[0] = int(file_set[0])
                file_set[1] = int(file_set[1])
                if len(file_set) != 2:
                    raise ValueError
                file_set = tuple(file_set)
            elif setting in ["library_width", "slideshow_delay",
                             "file_check_amount", "commandline_padding",
                             "completion_height"]:
                # Must be an integer
                file_set = int(section[setting])
            elif setting == "border_width":
                file_set = int(section[setting])
            elif setting == "desktop_start_dir":
                file_set = os.path.expanduser(section[setting])
                # Do not change the setting if the directory doesn't exist
                if not os.path.isdir(file_set):
                    continue
            elif setting == "markup":
                # Must be valid markup, not completely safe but better than
                # nothing
                markup_str = section[setting]
                if not markup_str.startswith("<span ") \
                        or not markup_str.endswith(">"):
                    continue
                file_set = section[setting]
            else:
                file_set = section.getboolean(setting)

            settings[key][setting] = file_set
        except ValueError:
            message += "Invalid setting '%s' for '%s'.\n" \
                "Falling back to default '%s'.\n\n" \
                % (section[setting], setting, settings[key][setting])
    return settings, message


def add_aliases(config, settings):
    """Add aliases from the configfile to the ALIASES section of settings.

    Args:
        config: configparser.ConfigParser of the configfile.
        settings: Dictionary of settings to operate on.

    Return:
        settings: Dictionary of modified settings.
        message: Error message filled with aliases that cannot be parsed.
    """
    message = ""

    try:
        alias_section = config["ALIASES"]
    except KeyError:
        # Default to no aliases if the section does not exist in the configfile
        alias_section = dict()

    for alias in alias_section.keys():
        try:
            settings["ALIASES"][alias] = alias_section[alias]
        except configparser.InterpolationError as e:
            message += e.message + ".\nParsing alias '" + alias + "' failed." \
                + "\nIf you meant to use % for current file, use %%."

    return settings, message


def parse_config(local_config="~/.vimiv/vimivrc",
                 system_config="/etc/vimiv/vimivrc",
                 running_tests=False):
    """Check each configfile for settings and apply them.

    Args:
        running_tests: If True running from testsuite. Do not show error popup.
    Return:
        Dictionary of modified settings.
    """
    settings = set_defaults()
    possible_configfiles = [system_config, local_config]
    configfiles = [os.path.expanduser(configfile)
                   for configfile in possible_configfiles
                   if configfile
                   and os.path.isfile(os.path.expanduser(configfile))]
    # Error message, gets filled with invalid sections in the user's configfile.
    # If any exist, a popup is displayed at startup.
    message = ""

    # Iterate through the configfiles overwriting settings accordingly
    for configfile in configfiles:
        config = configparser.ConfigParser()
        try:
            config.read(configfile)
        except UnicodeDecodeError:
            message += "Could not decode configfile " + configfile
            continue
        except configparser.MissingSectionHeaderError:
            message += "Invalid configfile " + configfile
            continue
        except configparser.ParsingError as e:
            message += str(e)
            continue

        keys = [key for key in config.keys() if key in ["GENERAL", "LIBRARY"]]
        for key in keys:
            settings, partial_message = overwrite_section(key, config, settings)
            message += partial_message
        settings, partial_message = add_aliases(config, settings)
        message += partial_message

    if message:
        error_message(message, running_tests=running_tests)
    return settings


def parse_keys(running_tests=False):
    """Check for a keyfile and parse it.

    Args:
        running_tests: If True running from testsuite. Do not show error popup.
    Return:
        Dictionary of keybindings.
    """
    # Check which keyfile should be used
    keys = configparser.ConfigParser()
    try:
        if os.path.isfile(os.path.expanduser("~/.vimiv/keys.conf")):
            keys.read(os.path.expanduser("~/.vimiv/keys.conf"))
        elif os.path.isfile("/etc/vimiv/keys.conf"):
            keys.read("/etc/vimiv/keys.conf")
        else:
            message = "Keyfile not found. Exiting."
            error_message(message)
            sys.exit(1)
    except configparser.DuplicateOptionError as e:
        message = e.message + ".\n Duplicate keybinding. Exiting."
        error_message(message)
        sys.exit(1)

    # Get the keybinding dictionaries checking for errors
    try:
        keys_image = keys["IMAGE"]
        keys_thumbnail = keys["THUMBNAIL"]
        keys_library = keys["LIBRARY"]
        keys_manipulate = keys["MANIPULATE"]
        keys_command = keys["COMMAND"]
    except KeyError as e:
        message = "Missing section " + str(e) + " in keys.conf.\n" \
                  + "Refer to vimivrc(5) to fix your config."
        error_message(message, running_tests=running_tests)
        sys.exit(1)

    # Update the dictionaries of every window with the keybindings that apply
    # for more than one window
    keys_image.update(keys["GENERAL"])
    keys_image.update(keys["IM_THUMB"])
    keys_image.update(keys["IM_LIB"])
    keys_thumbnail.update(keys["GENERAL"])
    keys_thumbnail.update(keys["IM_THUMB"])
    keys_library.update(keys["GENERAL"])
    keys_library.update(keys["IM_LIB"])

    # Generate one dictionary for all and return it
    keybindings = {"IMAGE": keys_image,
                   "THUMBNAIL": keys_thumbnail,
                   "LIBRARY": keys_library,
                   "MANIPULATE": keys_manipulate,
                   "COMMAND": keys_command}
    return keybindings


def parse_dirs(basedir):
    """Check for and create all required directories basedir.

    Args:
        basedir: The base directory of vimiv. ~/.vimiv or mkdtemp()
    """
    vimivdir = os.path.expanduser(basedir)
    tagdir = os.path.join(vimivdir, "Tags")
    thumbdir = os.path.join(vimivdir, "Thumbnails")
    trashdir = os.path.join(vimivdir, "Trash")
    dirs = [vimivdir, tagdir, thumbdir, trashdir]

    for directory in dirs:
        if not os.path.isdir(directory):
            os.mkdir(directory)
