#!/usr/bin/env python3
# encoding: utf-8
""" Return a list of images for vimiv """

import imghdr
import os
import shutil
from PIL import Image
from random import shuffle
from vimiv.helpers import listdir_wrapper

# Directory for trash
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
trashdir = os.path.join(vimivdir, "Trash")

def recursive_search(directory):
    """ Search a directory recursively for images """
    for root, dirs, files in os.walk(directory):
        for fil in files:
            yield os.path.join(root, fil)

def populate_single(arg, recursive):
    """ Populate a complete filelist if only one path is given """
    if os.path.isfile(arg):
        # Use parent directory
        directory = os.path.dirname(arg)
        args = listdir_wrapper(directory)
        for i, arg in enumerate(args):
            args[i] = os.path.join(directory, arg)

        return 0, args  # Success and the created filelist

    elif os.path.isdir(arg):
        if recursive:
            args = sorted(recursive_search(arg))
            return 0, args
        else:
            return 1, arg  # Failure and the directory


def populate(args, recursive=False, shuffle_paths=False):
    """ Populate a list of files out of a given path """
    paths = []
    # Default to current directory for recursive search
    if not args and recursive:
        args = [os.path.abspath(".")]
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
             if is_image(possible_path)]

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
    for im in filelist:
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

def test_svg(h, b):
    """ svg data """
    try:
        last_line = b.readlines()[-1].decode("utf-8")
        if last_line == '</svg>\n':
            return "svg"
    except:
        return None

def is_image(filename):
    """ Checks whether the file is an image """
    imghdr.tests.append(test_svg)
    complete_name = os.path.abspath(os.path.expanduser(filename))
    if not os.path.exists(complete_name):
        return False
    elif os.path.isdir(complete_name):
        return False
    elif imghdr.what(complete_name):
        return True
    else:
        return False

class FileExtras(object):
    """ Extra fileactions for vimiv """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv

    def clear(self, directory):
        """ Remove all files in directory (Trash or Thumbnails) """
        for fil in os.listdir(trashdir):
            fil = os.path.join(trashdir, fil)
            os.remove(fil)

    def format_files(self, string):
        """ Format the image names in the filelist according to a formatstring
            nicely numbering them """
        if not self.vimiv.paths:
            self.vimiv.statusbar.err_message("No files in path")
            return

        # Check if exifdata is available and needed
        tofind = ("%" in string)
        if tofind:
            try:
                for fil in self.vimiv.paths:
                    im = Image.open(fil)
                    exif = im._getexif()
                    if not (exif and 306 in exif):
                        raise AttributeError
            except:
                self.vimiv.statusbar.err_message("No exif data for %s available"
                                                 % (fil))
                return

        for i, fil in enumerate(self.vimiv.paths):
            ending = fil.split(".")[-1]
            num = "%03d" % (i+1)
            # Exif stuff
            if tofind:
                im = Image.open(fil)
                exif = im._getexif()
                date = exif[306]
                time = date.split()[1].split(":")
                date = date.split()[0].split(":")
                outstring = string.replace("%Y", date[0])  # year
                outstring = outstring.replace("%m", date[1])  # month
                outstring = outstring.replace("%d", date[2])  # day
                outstring = outstring.replace("%H", time[0])  # hour
                outstring = outstring.replace("%M", time[1])  # minute
                outstring = outstring.replace("%S", time[2])  # second
            else:
                outstring = string
            # Ending
            outstring += num + "." + ending
            shutil.move(fil, outstring)

        # Reload everything
        self.reload_changes(os.path.abspath("."), True)

    def reload_changes(self, directory, reload_path=True, pipe=False,
                       pipe_input=None):
        """ Reload everything, meaning filelist in library and image """
        if (directory == os.path.abspath(".") and directory !=
                self.vimiv.tags.directory and self.vimiv.library.toggled):
            if (self.vimiv.library.treepos >= 0 and
                    self.vimiv.library.treepos <=
                    len(self.vimiv.library.files)):
                self.vimiv.library.remember_pos(directory,
                                                self.vimiv.library.treepos)
            self.vimiv.library.reload(directory)
        if self.vimiv.paths and reload_path:
            pathdir = os.path.dirname(self.vimiv.paths[self.vimiv.index])
            files = sorted(os.listdir(pathdir))
            for i, fil in enumerate(files):
                files[i] = os.path.join(pathdir, fil)
            # Remember current pos
            self.vimiv.keyhandler.num_str = str(self.vimiv.index + 1)
            self.vimiv.paths, self.vimiv.index = populate(files)
            self.vimiv.image.move_pos()
            if self.vimiv.library.expand and not self.vimiv.paths:
                self.vimiv.library.grid.set_size_request(self.vimiv.winsize[0],
                                                         10)
            if self.vimiv.thumbnail.toggled:
                for i, image in self.vimiv.paths:
                    self.vimiv.thumbnail.reload(image, i, False)
        # Run the pipe
        if pipe:
            self.vimiv.commandline.pipe(pipe_input)
        return False  # To stop the timer
