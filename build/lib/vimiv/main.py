#!/usr/bin/env python
# encoding: utf-8
""" Main function for the vimiv image browser
Parses the necessary stuff and starts the Gtk instance """

import signal
from vimiv.gtk import Vimiv
from vimiv.parser import get_args, parse_dirs, parse_config, parse_args
from vimiv.fileactions import populate


def main():
    """ Starting point for vimiv """
    parser = get_args()
    parse_dirs()
    settings = parse_config()
    settings = parse_args(parser, settings)

    # Get the correct path
    if settings["GENERAL"]["start_from_desktop"]:
        args = ["GENERAL"]["desktop_start_dir"]
    else:
        args = settings["GENERAL"]["paths"]

    # Recursive and shuffling requiered immediately by populate
    recursive = settings["GENERAL"]["recursive"]
    shuffle_paths = settings["GENERAL"]["shuffle"]

    paths, index = populate(args, recursive, shuffle_paths)

    # Start the actual window
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    Vimiv(settings, paths, index).main()
