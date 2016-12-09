#!/usr/bin/env python3
# encoding: utf-8
"""All parsers for vimiv."""
import argparse
import configparser
import os
import sys
from vimiv.helpers import error_message
from vimiv.information import Information


def create_parser():
    """Create the argparse parser and return it.

    Return:
        argparse.ArgumentParser with the possible arguments.
    """
    usage = '%(prog)s [options] [paths ...]'
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("-b", "--bar", action="store_true", dest="sbar",
                        help="display statusbar")
    parser.add_argument("-B", "--no-bar", action="store_true", dest="hide_sbar",
                        help="hide statusbar")
    parser.add_argument("-l", "--library", action="store_true",
                        dest="library", help="display library")
    parser.add_argument("-L", "--no-library", action="store_true",
                        dest="hide_library", help="don't display library")
    parser.add_argument("-f", "--fullscreen", action="store_true",
                        dest="fullscreen", help="start in fullscreen")
    parser.add_argument("-F", "--no-fullscreen", action="store_true",
                        dest="no_fullscreen", help="don't start in fullscreen")
    parser.add_argument("-s", "--shuffle", action="store_true",
                        dest="shuffle", help="shuffle filelist")
    parser.add_argument("-S", "--no-shuffle", action="store_true",
                        dest="no_shuffle", help="don't shuffle the filelist")
    parser.add_argument("-r", "--recursive", action="store_true",
                        dest="recursive",
                        help="search given directories recursively")
    parser.add_argument("-R", "--no-recursive", action="store_true",
                        dest="no_recursive",
                        help="don't search given directories recursively")
    parser.add_argument("-v", "--version", action="store_true",
                        dest="show_version",
                        help="print version information and exit")
    parser.add_argument("--slideshow", action="store_true",
                        help="start slideshow immediately")
    parser.add_argument("--start-from-desktop", action="store_true",
                        help="start using the desktop_start_dir as path",
                        dest="desktop")
    parser.add_argument("--slideshow-delay", type=float,
                        help="set the slideshow delay")
    parser.add_argument("-g", "--geometry", dest="geometry",
                        help="set the starting geometry")
    parser.add_argument("path", nargs="*", default=[])

    return parser


def parse_args(parser, settings, arguments):
    """Parse the arguments and return the modified settings.

    Args:
        parser: argparse.ArgumentParser with the possible arguments.
        settings: Dictionary containing all settings.
        arguments: Extra arguments to add to the parser.

    Return: Modified settings after parsing the arguments.
    """
    args = parser.parse_args(arguments)
    if args.show_version:
        information = Information()
        print(information.get_version())
        sys.exit(0)
    if args.sbar:
        settings["GENERAL"]["display_bar"] = True
    if args.hide_sbar:
        settings["GENERAL"]["display_bar"] = False
    if args.recursive:
        settings["GENERAL"]["recursive"] = True
    if args.no_recursive:
        settings["GENERAL"]["recursive"] = False
    if args.fullscreen:
        settings["GENERAL"]["start_fullscreen"] = True
    if args.no_fullscreen:
        settings["GENERAL"]["start_fullscreen"] = False
    if args.shuffle:
        settings["GENERAL"]["shuffle"] = True
    if args.no_shuffle:
        settings["GENERAL"]["shuffle"] = False
    if args.slideshow_delay:
        settings["GENERAL"]["slideshow_delay"] = args.slideshow_delay
    if args.slideshow:
        settings["GENERAL"]["start_slideshow"] = True
    if args.geometry:
        settings["GENERAL"]["geometry"] = args.geometry
    if args.library:
        settings["LIBRARY"]["show_library"] = True
    if args.hide_library:
        settings["LIBRARY"]["show_library"] = False

    settings["GENERAL"]["start_from_desktop"] = args.desktop
    # Startup from desktop
    if args.desktop:
        if args.path:
            paths = args.path
        else:
            paths = [settings["LIBRARY"]["desktop_start_dir"]]
    # Be able to read files from a stdin pipe
    elif not sys.stdin.isatty():
        paths = []
        for line in sys.stdin:
            paths.append(line.rstrip("\n"))
        # Fall back to args.path if nothing was found
        if not paths:
            paths = args.path
    else:
        paths = args.path

    settings["GENERAL"]["paths"] = paths

    return settings


def check_configs(filelist):
    """Return the existing configfiles in a list.

    Args:
        filelist: List of possible configfiles.

    Return: List of existing configfiles.
    """
    configfiles = []
    for fil in filelist:
        if os.path.isfile(fil):
            configfiles.append(fil)

    return configfiles


def set_defaults():
    """Return the default settings for vimiv.

    Return: Dictionary of default settings.
    """
    general = {"fullscreen": False,
               "slideshow": False,
               "slideshow_delay": 2,
               "shuffle": False,
               "display_bar": True,
               "thumbsize": (128, 128),
               "thumb_maxsize": (256, 256),
               "geometry": (800, 600),
               "search_case_sensitive": True,
               "recursive": False,
               "rescale_svg": True,
               "overzoom": False,
               "cache_thumbnails": True}
    library = {"show_library": False,
               "library_width": 300,
               "expand_lib": True,
               "border_width": 0,
               "markup": '<span foreground="#00FF00">',
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
                             "file_check_amount"]:
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


def parse_config():
    """Check each configfile for settings and apply them.

    Return: Dictionary of modified settings.
    """
    settings = set_defaults()
    configfiles = check_configs(["/etc/vimiv/vimivrc",
                                 os.path.expanduser("~/.vimiv/vimivrc")])
    # Error message, gets filled with invalid sections in the user's configfile.
    # If any exist, a popup is displayed at startup.
    message = ""

    # Iterate through the configfiles overwriting settings accordingly
    for configfile in configfiles:
        config = configparser.ConfigParser()
        config.read(configfile)
        keys = [key for key in config.keys() if key in ["GENERAL", "LIBRARY"]]
        for key in keys:
            settings, partial_message = overwrite_section(key, config, settings)
            message += partial_message
        settings, partial_message = add_aliases(config, settings)
        message += partial_message

    if message:
        error_message(message)
    return settings


def parse_keys():
    """Check for a keyfile and parse it.

    Return: Dictionary of keybindings.
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
        error_message(message)
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


def parse_dirs():
    """Check for and create all required directories in ~/.vimiv."""
    vimivdir = os.path.expanduser("~/.vimiv")
    tagdir = os.path.join(vimivdir, "Tags")
    thumbdir = os.path.join(vimivdir, "Thumbnails")
    trashdir = os.path.join(vimivdir, "Trash")
    dirs = [vimivdir, tagdir, thumbdir, trashdir]

    for directory in dirs:
        if not os.path.isdir(directory):
            os.mkdir(directory)
