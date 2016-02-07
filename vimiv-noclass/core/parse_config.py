#!/usr/bin/env python
# encoding: utf-8
""" Checks for the configuration files and sets defaults if none exist """
import os.path
import configparser


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

parse_config()
