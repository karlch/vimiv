#!/usr/bin/env python
# encoding: utf-8
""" Return a list of images for vimiv """

import mimetypes
import os
from random import shuffle
# from vimiv.fileactions.fileactions import recursive_search  # TODO
from vimiv.helpers.helpers import listdir_wrapper
from vimiv.helpers.variables import types
# from vimiv.library.libfuncs import move_up  # TODO


def populate_single(arg, recursive):
    """ Populate a complete filelist if only one path is given """
    if os.path.isfile(arg):
        # Use parent directory and realpath
        single = os.path.realpath(arg)
        directory = os.path.dirname(single)
        args = sorted(list(listdir_wrapper(directory)))
        for i, arg in enumerate(args):
            args[i] = os.path.join(directory, arg)

        return args
    elif os.path.isdir(arg) and not recursive:
        # Open dir in library browser
        move_up(arg, True)

        return 0


def populate(args, settings):
    """ Populate a list of files out of a given path """
    recursive = settings["GENERAL"]["recursive"]
    shuffle_paths = settings["GENERAL"]["shuffle"]
    paths = []
    # If only one path is passed do special stuff
    single = None
    if len(args) == 1:
        single = args[0]
        args = populate_single(single, recursive)

    # Add everything
    for arg in args:
        path = os.path.abspath(arg)
        if os.path.isfile(path):
            paths.append(path)
        elif os.path.isdir(path) and recursive:
            recursive_search(path)
    # Remove unsupported files
    paths = [possible_path for possible_path in paths
             if mimetypes.guess_type(possible_path)[0] in types]

    # Shuffle
    if shuffle_paths:
        shuffle(paths)

    # Complete special stuff for single arg
    if single and single in paths:
        index = paths.index(single)
    else:
        index = 0

    return paths, index
