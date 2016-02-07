#!/usr/bin/env python
# encoding: utf-8
""" Return a list of images for vimiv """

import mimetypes
import os
from random import shuffle
from vimiv.helpers import listdir_wrapper
from vimiv.variables import types
# from vimiv.library.libfuncs import move_up  # TODO


def recursive_search(directory):
    """ Search a directory recursively for images """
    paths = listdir_wrapper(directory)
    for path in paths:
        path = os.path.join(dir, path)
        if os.path.isfile(path):
            paths.append(path)
        else:
            recursive_search(path)

    return paths


def populate_single(arg, recursive):
    """ Populate a complete filelist if only one path is given """
    if os.path.isfile(arg):
        # Use parent directory and realpath
        single = os.path.realpath(arg)
        directory = os.path.dirname(single)
        args = listdir_wrapper(directory)
        for i, arg in enumerate(args):
            args[i] = os.path.join(directory, arg)

        return args

    elif os.path.isdir(arg) and not recursive:
        # Open dir in library browser
        move_up(arg, True)

        return 0


def populate(args, recursive=False, shuffle_paths=False):
    """ Populate a list of files out of a given path """
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
            paths = recursive_search(path)
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
