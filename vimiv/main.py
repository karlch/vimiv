#!/usr/bin/env python3
# encoding: utf-8
"""Main function for the vimiv["image"] browser.

Parses the necessary stuff and starts the Gtk instance.
"""

import signal
from vimiv.parser import get_args, parse_dirs, parse_config, parse_args
from vimiv.fileactions import populate
from vimiv.app import Vimiv

def main(arguments, vimiv_id="org.vimiv"):
    """Starting point for vimiv.

    Args:
        arguments: Arguments passed to the commandline.
        vimiv_id: The ID used to register vimiv.
    Return:
        The generated main vimiv application.
    """
    parser = get_args()
    parse_dirs()
    settings = parse_config()
    settings = parse_args(parser, settings, arguments)

    args = settings["GENERAL"]["paths"]

    # Recursive and shuffling required immediately by populate
    recursive = settings["GENERAL"]["recursive"]
    shuffle_paths = settings["GENERAL"]["shuffle"]

    paths, index = populate(args, recursive, shuffle_paths)
    # Start the actual window
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    vimiv = Vimiv(vimiv_id)
    vimiv.set_settings(settings)
    vimiv.set_paths(paths, index)
    return vimiv
