#!/usr/bin/env python3
# encoding: utf-8
"""Different actions applying directly to files."""

import os
import shutil
from random import shuffle
from PIL import Image
from gi.repository import GdkPixbuf, Gtk, Gdk
from vimiv.helpers import listdir_wrapper


def recursive_search(directory):
    """Search a directory recursively for images.

    Args:
        directory: Directory to search for images.
    Return:
        List of images in directory.
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
    Return:
        Generated list of paths.
    """
    paths = []
    if os.path.isfile(arg):
        # Use parent directory
        directory = os.path.dirname(arg)
        if not directory:  # Default to current directory
            directory = "./"
        basename = os.path.basename(arg)
        paths = listdir_wrapper(directory)
        # Set the argument to the beginning of the list
        pos = paths.index(basename)
        paths = [os.path.join(directory, path)
                 for path in paths[pos:] + paths[:pos]]
    elif os.path.isdir(arg) and recursive:
        paths = sorted(recursive_search(arg))
    return paths


def populate(args, recursive=False, shuffle_paths=False):
    """Populate a list of files out given paths.

    Args:
        args: Paths given.
        recursive: If True search path recursively for images.
        shuffle_paths: If True shuffle found paths randomly.
    Return:
        Found paths, position of first given path.
    """
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
            paths = list(recursive_search(path))
    # Remove unsupported files
    paths = [possible_path for possible_path in paths
             if is_image(possible_path)]

    # Shuffle
    if shuffle_paths:
        shuffle(paths)

    return paths, 0


def move_to_trash(filelist, trashdir):
    """Move every file in filelist to the Trash.

    If it is a directory, an error is thrown.

    Args:
        filelist: The list of files to operate on.
        trashdir: The directory to move the files to.
    """
    # Create the directory if it isn't there yet
    if not os.path.isdir(trashdir):
        os.mkdir(trashdir)

    # Loop over every file
    for im in filelist:
        if os.path.isdir(im):
            return 1  # Error
        if os.path.exists(im):
            # Check if there is already a file with that name in the trash
            # If so, add numbers to the filename until it doesn't exist anymore
            delfile = os.path.join(trashdir, os.path.basename(im))
            if os.path.exists(delfile):
                backnum = 1
                ndelfile = delfile + "." + str(backnum)
                while os.path.exists(ndelfile):
                    backnum += 1
                    ndelfile = delfile + "." + str(backnum)
                os.rename(delfile, ndelfile)
            shutil.move(im, trashdir)

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

    def __init__(self, app):
        """Receive and set main vimiv application.

        Args:
            app: The main vimiv class to interact with.
            clipboard: Gtk Clipboard depending on config.
        """
        self.app = app
        self.use_primary = self.app.settings["GENERAL"]["copy_to_primary"]

    def clear(self, directory_name):
        """Remove all files in directory (Trash or Thumbnails).

        Args:
            directory_name: Directory to clear.
        """
        if directory_name == "Trash":
            directory = self.app["image"].trashdir
        else:
            directory = self.app["thumbnail"].directory
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
        if self.app["library"].treeview.is_focus():
            message = "Format only works on opened image files"
            self.app["statusbar"].message(message, "info")
            return
        if not self.app.paths:
            self.app["statusbar"].message("No files in path", "info")
            return

        # Check if exifdata is available and needed
        tofind = ("%" in string)
        if tofind:
            try:
                for fil in self.app.paths:
                    with Image.open(fil) as im:
                        exif = im._getexif()
                        if not (exif and 306 in exif):
                            raise AttributeError
            except AttributeError:
                self.app["statusbar"].message(
                    "No exif data for %s available" % (fil), "error")
                return

        for i, fil in enumerate(self.app.paths):
            ending = os.path.splitext(fil)[1]
            num = "%03d" % (i + 1)
            # Exif stuff
            if tofind:
                with Image.open(fil) as im:
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
        # Reload library remembering position
        if (directory == os.getcwd() and directory != self.app["tags"].directory
                and self.app["library"].grid.is_visible()):
            old_pos_lib = self.app.get_pos(False, "lib")
            if old_pos_lib >= 0 and \
                    old_pos_lib <= len(self.app["library"].files):
                self.app["library"].remember_pos(directory, old_pos_lib)
            self.app["library"].reload(directory)
            # Refocus other widgets is necessary
            if self.app["window"].last_focused == "im":
                self.app["image"].scrolled_win.grab_focus()
            elif self.app["window"].last_focused == "thu":
                self.app["thumbnail"].iconview.grab_focus()
        # Reload image/thumbnail
        if self.app.paths and reload_path:
            old_pos_im = self.app.get_pos(False, "im")
            # Get all files in directory again
            pathdir = os.path.dirname(self.app.paths[old_pos_im])
            files = sorted(os.listdir(pathdir))
            for i, fil in enumerate(files):
                files[i] = os.path.join(pathdir, fil)
            self.app.paths, self.app.index = populate(files)
            # Expand library if set by user and all paths were removed
            if self.app["library"].expand and not self.app.paths:
                self.app["library"].treeview.set_hexpand(True)
            # Refocus the current position
            if self.app["thumbnail"].toggled:
                old_pos_thu = self.app.get_pos(False, "thu")
                for i, image in enumerate(self.app.paths):
                    self.app["thumbnail"].reload(image, i, False)
                self.app["thumbnail"].move_to_pos(old_pos_thu)
            else:
                self.app["keyhandler"].num_str = str(old_pos_im + 1)
                self.app["image"].move_pos()
        # Run the pipe
        if pipe:
            self.app["commandline"].pipe(pipe_input)
        return False  # To stop the timer

    def copy_name(self, abspath=False):
        """Copy image name to clipboard.

        Args:
            abspath: Use absolute path or only the basename.
        """
        # Get name to copy
        name = self.app.get_pos(True)
        if abspath:
            name = os.path.abspath(name)
        else:
            name = os.path.basename(name)
        # Set clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY) \
            if self.use_primary \
            else Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        # Text to clipboard
        clipboard.set_text(name, -1)
        # Info message
        message = "Copied <b>" + name + "</b> to %s" % \
            ("primary" if self.use_primary else "clipboard")
        self.app["statusbar"].message(message, "info")

    def toggle_clipboard(self):
        """Toggle between primary and clipboard selection."""
        self.use_primary = not self.use_primary
