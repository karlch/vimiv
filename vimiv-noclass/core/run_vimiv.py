#!/usr/bin/env python
# encoding: utf-8
""" Initializes the actual program """

import signal
from vimiv.fileactions import populate
from vimiv.gtk import gtk


def run(settings):
    """ Run vimiv """
    if settings["GENERAL"]["start_from_desktop"]:
        args = ["GENERAL"]["desktop_start_dir"]
    else:
        args = settings["GENERAL"]["paths"]

    paths, index = populate.populate(args, settings)

    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    gtk.Vimiv(settings, paths, index).main()
