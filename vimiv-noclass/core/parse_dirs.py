#!/usr/bin/env python
# encoding: utf-8
""" Checks whether the necessary directory ~/.vimiv and all of the
subdirectories exist and creates all of those that aren't there """

import os


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
