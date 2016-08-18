#!/usr/bin/env python3
# encoding: utf-8
"""Different actions applying directly to files."""

import os
import shutil
from random import shuffle
from PIL import Image
from gi.repository import GdkPixbuf
from vimiv.helpers import listdir_wrapper

# Directory for trash
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
trashdir = os.path.join(vimivdir, "Trash")
thumbdir = os.path.join(vimivdir, "Thumbnails")


def recursive_search(directory):
    """Search a directory recursively for images.

    Args:
        directory: Directory to search for images.
    Return: List of images in directory.
    """
    # pylint: disable=unused-variable
    for root, dirs, files in os.walk(directory):
        for fil in files:
            yield os.path.join(root, fil)


def populate_single(arg, recursive):
    """Populate a complete filelist if only one path is given.

    Args:
        arg: Single path given.
        recursive: If True search path recursively for images.
    """
    if os.path.isfile(arg):
        # Use parent directory
        directory = os.path.dirname(os.path.abspath(arg))
        basename = os.path.basename(os.path.abspath(arg))
        args = listdir_wrapper(directory)
        # Set the argument to the beginning of the list
        pos = args.index(basename)
        args = args[pos:] + args[:pos]
        for i, arg in enumerate(args):
            args[i] = os.path.join(directory, arg)

        return 0, args  # Success and the created filelist

    elif os.path.isdir(arg):
        if recursive:
            args = sorted(recursive_search(arg))
            return 0, args
        else:
            return 1, arg  # Failure and the directory

    else:
        return 1, "."  # Does not exist, use current directory


def populate(args, recursive=False, shuffle_paths=False):
    """Populate a list of files out given paths.

    Args:
        args: Paths given.
        recursive: If True search path recursively for images.
        shuffle_paths: If True shuffle found paths randomly.
    Return: Found paths, position of first given path.
    """
    paths = []
    # Default to current directory for recursive search
    if not args and recursive:
        args = [os.getcwd()]
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
            paths = list(recursive_search(path))
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


def move_to_trash(filelist):
    """Move every file in filelist to the Trash.

    If it is a directory, an error is thrown.

    Args:
        filelist: The list of files to operate on.
    """
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
                ndelfile = delfile + "." + str(backnum)
                while os.path.exists(ndelfile):
                    backnum += 1
                    ndelfile = delfile + "." + str(backnum)
                os.rename(delfile, ndelfile)
            shutil.move(im, deldir)

        return 0  # Success


def is_image(filename):
    """Check whether a file is an image.

    Args:
        filename: Name of file to check.
    """
    complete_name = os.path.abspath(os.path.expanduser(filename))
    try:
        return bool(GdkPixbuf.Pixbuf.get_file_info(complete_name)[0])
    except:
        return False


class FileExtras(object):
    """Extra fileactions for vimiv."""

    def __init__(self, vimiv):
        """Receive and set vimiv class.

        Args:
            vimiv: The main vimiv class to interact with.
        """
        self.vimiv = vimiv

    def clear(self, directory_name):
        """Remove all files in directory (Trash or Thumbnails).

        Args:
            directory_name: Directory to clear.
        """
        if directory_name == "Trash":
            directory = trashdir
        else:
            directory = thumbdir
        for fil in os.listdir(directory):
            fil = os.path.join(directory, fil)
            os.remove(fil)

    def format_files(self, string):
        """Format image names in filelist according to a formatstring.

        Numbers files in form of formatstring_000.extension. Replaces exif
        information accordingly.

        Args:
            string: Formatstring to use.
        """
        # Catch problems
        if self.vimiv.library.treeview.is_focus():
            message = "Format only works on opened image files"
            self.vimiv.statusbar.err_message(message)
            return
        if not self.vimiv.paths:
            self.vimiv.statusbar.err_message("No files in path")
            return

        # Check if exifdata is available and needed
        tofind = ("%" in string)
        if tofind:
            try:
                for fil in self.vimiv.paths:
                    with open(fil) as image_file:
                        im = Image.open(image_file)
                        exif = im._getexif()
                        if not (exif and 306 in exif):
                            raise AttributeError
            except:
                self.vimiv.statusbar.err_message("No exif data for %s available"
                                                 % (fil))
                return

        for i, fil in enumerate(self.vimiv.paths):
            ending = os.path.splitext(fil)[1]
            num = "%03d" % (i + 1)
            # Exif stuff
            if tofind:
                with open(fil) as image_file:
                    im = Image.open(image_file)
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
            outstring += num + ending
            os.rename(fil, outstring)

        # Reload everything
        self.reload_changes(os.getcwd(), True)

    def reload_changes(self, directory, reload_path=True, pipe=False,
                       pipe_input=None):
        """Reload everything that could have changed.

        Reload filelist in library and image and update names accordingly.

        Args:
            directory: Directory which was affected.
            reload_path: If True reload information that contains the current
                path.
            pipe: If True, input came from a pipe. Therefore run pipe.
            pipe_input: Command that comes from pipe.
        """
        if (directory == os.getcwd() and directory !=
                self.vimiv.tags.directory and self.vimiv.library.toggled):
            if (self.vimiv.library.get_treepos() >= 0 and
                    self.vimiv.library.get_treepos() <=
                    len(self.vimiv.library.files)):
                self.vimiv.library.remember_pos(
                    directory, self.vimiv.library.get_treepos())
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
