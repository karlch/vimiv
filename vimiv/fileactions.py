#!/usr/bin/env python3
# encoding: utf-8
""" Return a list of images for vimiv """

import mimetypes
import os
import shutil
from random import shuffle
from vimiv.helpers import listdir_wrapper
from vimiv.variables import types


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

        return 0, args  # Success and the created filelist

    elif os.path.isdir(arg) and not recursive:
        return 1, arg  # Failure and the directory


def populate(args, recursive=False, shuffle_paths=False):
    """ Populate a list of files out of a given path """
    paths = []
    # If only one path is passed do special stuff
    single = None
    if len(args) == 1:
        single = args[0]
        error, args = populate_single(single, recursive)
        if error:
            return args, 0

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


def delete(filelist):
    """ Moves every file in filelist to the Trash. If it is a directory, an
    error is thrown."""
    # Create the directory if it isn't there yet
    deldir = os.path.expanduser("~/.vimiv/Trash")
    if not os.path.isdir(deldir):
        os.mkdir(deldir)

    # Loop over every file
    for i, im in enumerate(filelist):
        if os.path.isdir(im):
            return 1  # Error
        if os.path.exists(im):
            # Check if there is already a file with that name in the trash
            # If so, add numbers to the filename until it doesn't exist anymore
            delfile = os.path.join(deldir, os.path.basename(im))
            if os.path.exists(delfile):
                backnum = 1
                ndelfile = delfile+"."+str(backnum)
                while os.path.exists(ndelfile):
                    backnum += 1
                    ndelfile = delfile+"."+str(backnum)
                shutil.move(delfile, ndelfile)
            shutil.move(im, deldir)

        return 0  # Success
