#!/usr/bin/env python
# encoding: utf-8
""" All parsers for vimiv """
import argparse
import configparser
import os


def get_args():
    """ Create the argparse parser and return it """
    usage = '%(prog)s [options] [paths ...]'
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("-b", "--bar", action="store_true", dest="sbar",
                        help="display statusbar")
    parser.add_argument("-B", "--no-bar", action="store_false", dest="sbar",
                        help="hide statusbar")
    parser.add_argument("-l", "--library", action="store_true",
                        dest="library", help="display library")
    parser.add_argument("-L", "--no-library", action="store_false",
                        dest="library", help="don't display library")
    parser.add_argument("-f", "--fullscreen", action="store_true",
                        dest="fullscreen", help="start in fullscreen")
    parser.add_argument("-F", "--no-fullscreen", action="store_false",
                        dest="fullscreen", help="don't start in fullscreen")
    parser.add_argument("-s", "--shuffle", action="store_true",
                        dest="shuffle", help="shuffle filelist")
    parser.add_argument("-S", "--no-shuffle", action="store_false",
                        dest="shuffle", help="don't shuffle the filelist")
    parser.add_argument("-r", "--recursive", action="store_true",
                        dest="recursive",
                        help="search given directories recursively")
    parser.add_argument("-R", "--no-recursive", action="store_false",
                        dest="recursive",
                        help="don't search given directories recursively")
    parser.add_argument("--slideshow", action="store_true",
                        help="start slideshow immediately")
    parser.add_argument("--start-from-desktop", action="store_true",
                        help="start using the desktop_start_dir as path",
                        dest="desktop")
    parser.add_argument("--slideshow-delay", type=float,
                        help="set the slideshow delay")
    parser.add_argument("-g", "--geometry", dest="geometry",
                        help="set the starting geometry")
    parser.add_argument("path", nargs='*', default=[])

    return parser


def parse_args(parser, settings):
    """ Parse the arguments and return the modified settings """
    args = parser.parse_args()
    if args.sbar:
        settings["GENERAL"]["display_bar"] = args.sbar
    if args.recursive:
        settings["GENERAL"]["recursive"] = args.recursive
    if args.fullscreen:
        settings["GENERAL"]["start_fullscreen"] = args.fullscreen
    if args.shuffle:
        settings["GENERAL"]["shuffle"] = args.shuffle
    if args.slideshow_delay:
        settings["GENERAL"]["slideshow_delay"] = args.slideshow_delay
    if args.slideshow:
        settings["GENERAL"]["start_slideshow"] = args.slideshow
    if args.geometry:
        settings["GENERAL"]["geometry"] = args.geometry
    if args.library:
        settings["LIBRARY"]["show_library"] = args.library

    settings["GENERAL"]["start_from_desktop"] = args.desktop
    settings["GENERAL"]["paths"] = args.path

    return settings


def check_configs():
    """ Returns the existing configfiles in a list """
    configfiles = []
    if os.path.isfile("/etc/vimiv/vimivrc"):
        configfiles.append("/etc/vimiv/vimivrc")
    if os.path.isfile(os.path.expanduser("~/.vimiv/vimivrc")):
        configfiles.append(os.path.expanduser("~/.vimiv/vimivrc"))

    return configfiles


def set_defaults():
    """ Returns the default settings for vimiv """
    general = {"fullscreen": False,
               "slideshow": False,
               "slideshow_delay": 2,
               "shuffle": False,
               "display_bar": True,
               "thumbsize": (128, 128),
               "geometry": (800, 600),
               "recursive": False,
               "rescale_svg": True,
               "overzoom": False}
    library = {"show_library": False,
               "library_width": 300,
               "expand_lib": True,
               "border_width": 0,
               "border_color": "#000000",
               "show_hidden": False,
               "desktop_start_dir": os.path.expanduser("~")}
    settings = {"GENERAL": general, "LIBRARY": library}
    return settings


def overwrite_section(key, config, settings):
    """ Overwrites a section in settings with the available settings in a
    configfile """
    section = config[key]
    for setting in section.keys():
        # Parse the setting so it gets the correct value
        if setting == "geometry":
            try:
                file_set = (int(section[setting].split("x")[0]),
                            int(section[setting].split("x")[1]))
            except ValueError:
                continue
        elif setting == "thumbsize":
            file_set = section[setting].lstrip("(").rstrip(")")
            file_set = file_set.split(",")
            try:
                file_set[0] = int(file_set[0])
                file_set[1] = int(file_set[1])
                if len(file_set) != 2:
                    raise ValueError
            except ValueError:
                continue
        elif setting in ["library_width", "slideshow_delay"]:
            # Must be an integer
            try:
                file_set = int(section[setting])
            except ValueError:
                continue
        elif setting == "border_color":
            pass
        elif setting == "desktop_start_dir":
            file_set = os.path.expanduser(section[setting])
            # Do not change the setting if the directory doesn't exist
            if not os.path.isdir(file_set):
                continue
        else:
            file_set = section.getboolean(setting)

        settings[key][setting] = file_set

    return settings


def parse_config():
    """ Checks each configfile for settings and returns them accordingly """
    settings = set_defaults()
    configfiles = check_configs()

    # Iterate through the configfiles overwriting settings accordingly
    for configfile in configfiles:
        config = configparser.ConfigParser()
        config.read(configfile)
        keys = [key for key in config.keys() if key in ["GENERAL", "LIBRARY"]]
        for key in keys:
            settings = overwrite_section(key, config, settings)

    return settings


def parse_dirs():
    """ Checks for and creates all directories in ~/.vimiv """
    vimivdir = os.path.expanduser("~/.vimiv")
    tagdir = os.path.join(vimivdir, "Tags")
    thumbdir = os.path.join(vimivdir, "Thumbnails")
    trashdir = os.path.join(vimivdir, "Trash")
    dirs = [vimivdir, tagdir, thumbdir, trashdir]

    for directory in dirs:
        if not os.path.isdir(directory):
            os.mkdir(directory)
