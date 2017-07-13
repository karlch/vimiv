# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""All parsers for vimiv."""

import configparser
import os
import sys

from gi.repository import GLib
from vimiv.exceptions import SettingNotFoundError, WrongSettingValue
from vimiv.helpers import error_message
from vimiv.settings import settings


def get_aliases(config):
    """Add aliases from the configfile to the ALIASES section of settings.

    Args:
        config: configparser.ConfigParser of the configfile.

    Return:
        aliases: Dictionary of aliases.
        message: Error message filled with aliases that cannot be parsed.
    """
    message = ""
    aliases = {}

    try:
        alias_section = config["ALIASES"]
    except KeyError:
        # Default to no aliases if the section does not exist in the configfile
        alias_section = dict()

    for alias in alias_section:
        try:
            aliases[alias] = alias_section[alias]
        except configparser.InterpolationError as e:
            message += "Parsing alias '%s' failed.\n" % alias \
                + "If you meant to use % for current file, use %%.\n" \
                + e.message + "\n"

    return aliases, message


def parse_config(commandline_config=None, running_tests=False):
    """Check each configfile for settings and apply them.

    Args:
        commandline_config: Configfile given by command line flag to parse.
        running_tests: If True, running from testsuite.
    Return:
        Dictionary of modified settings.
    """
    configfiles = []
    # We do not want to parse user configuration files when running the test
    # suite
    if not running_tests:
        configfiles += [
            "/etc/vimiv/vimivrc",
            os.path.join(GLib.get_user_config_dir(), "vimiv/vimivrc"),
            os.path.expanduser("~/.vimiv/vimivrc")]
    if commandline_config:
        configfiles.append(commandline_config)

    # Error message, gets filled with invalid sections in the user's configfile.
    # If any exist, a popup is displayed at startup.
    message = ""

    # Let ConfigParser parse the list of configuration files
    config = configparser.ConfigParser()
    try:
        config.read(configfiles)
    except UnicodeDecodeError as e:
        message += "Could not decode configfile.\n" + str(e)
    except configparser.MissingSectionHeaderError as e:
        message += "Invalid configfile.\n" + str(e)
    except configparser.ParsingError as e:
        message += str(e)

    # Override settings with settings in config
    for header in ["GENERAL", "LIBRARY", "EDIT"]:
        if header not in config:
            continue
        section = config[header]
        for setting in section:
            try:
                settings.override(setting, section[setting])
            except WrongSettingValue as e:
                message += str(e) + "\n"
            except SettingNotFoundError:
                message += "Unknown setting %s\n" % (setting)

    # Receive aliases
    aliases, partial_message = get_aliases(config)
    settings.set_aliases(aliases)
    message += partial_message

    if message:
        error_message(message, running_tests=running_tests)
    return settings


def parse_keys(keyfiles=None, running_tests=False):
    """Check for a keyfile and parse it.

    Args:
        keyfiles: List of keybinding files. If not None, use this list instead
            of the default files.
        running_tests: If True running from testsuite. Do not show error popup.
    Return:
        Dictionary of keybindings.
    """
    if not keyfiles:
        keyfiles = \
            ["/etc/vimiv/keys.conf",
             os.path.join(GLib.get_user_config_dir(), "vimiv/keys.conf"),
             os.path.expanduser("~/.vimiv/keys.conf")]
    # Read the list of files
    keys = configparser.ConfigParser()
    try:
        # No file for keybindings found
        if not keys.read(keyfiles):
            message = "Keyfile not found. Exiting."
            error_message(message, running_tests=running_tests)
            sys.exit(1)
    except configparser.DuplicateOptionError as e:
        message = e.message + ".\n Duplicate keybinding. Exiting."
        error_message(message, running_tests=running_tests)
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
                  "Refer to vimivrc(5) to fix your config."
        error_message(message, running_tests=running_tests)
        sys.exit(1)

    # Update the dictionaries of every window with the keybindings that apply
    # for more than one window
    def update_keybindings(sections, keydict):
        """Add keybindings from generic sections to keydict."""
        for section in sections:
            if section in keys:
                print("Section", section, "is deprecated and will be removed in"
                      " a future version.")
                keydict.update(keys[section])
    update_keybindings(["GENERAL", "IM_THUMB", "IM_LIB"], keys_image)
    update_keybindings(["GENERAL", "IM_THUMB"], keys_thumbnail)
    update_keybindings(["GENERAL", "IM_LIB"], keys_library)

    # Generate one dictionary for all and return it
    keybindings = {"IMAGE": keys_image,
                   "THUMBNAIL": keys_thumbnail,
                   "LIBRARY": keys_library,
                   "MANIPULATE": keys_manipulate,
                   "COMMAND": keys_command}
    return keybindings
