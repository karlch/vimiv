# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Different actions applying directly to files."""

import os
from random import shuffle

from gi.repository import Gdk, GdkPixbuf, Gtk
from PIL import Image
from vimiv.helpers import listdir_wrapper


def recursive_search(directory):
    """Search a directory recursively for images.

    Args:
        directory: Directory to search for images.
    Return:
        List of images in directory.
    """
    for root, _, files in os.walk(directory):
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
        paths = listdir_wrapper(directory)
        paths = [os.path.join(directory, path) for path in paths]
        # Set the argument to the beginning of the list
    elif os.path.isdir(arg) and recursive:
        paths = sorted(recursive_search(arg))
    return paths


def populate(args, recursive=False, shuffle_paths=False, expand_single=True):
    """Populate a list of files out given paths.

    Args:
        args: Paths given.
        recursive: If True search path recursively for images.
        shuffle_paths: If True shuffle found paths randomly.
        expand_single: If True, populate a complete filelist with images from
            the same directory as the single argument given.
    Return:
        Found paths, position of first given path.
    """
    paths = []
    index = 0
    # If only one path is passed do special stuff
    first_path = os.path.abspath(args[0]) if args else None
    if len(args) == 1 and expand_single:
        args = populate_single(first_path, recursive)

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
    index = paths.index(first_path) if first_path in paths else 0

    # Shuffle
    if shuffle_paths:
        shuffle(paths)

    return paths, index


def is_image(filename):
    """Check whether a file is an image.

    Args:
        filename: Name of file to check.
    """
    complete_name = os.path.abspath(os.path.expanduser(filename))
    return bool(GdkPixbuf.Pixbuf.get_file_info(complete_name)[0])


def is_animation(filename):
    """Check whether a file is an animated image.

    Args:
        filename: Name of file to check.
    """
    complete_name = os.path.abspath(os.path.expanduser(filename))
    info = GdkPixbuf.Pixbuf.get_file_info(complete_name)[0]
    return "gif" in info.get_extensions()


class FileExtras(object):
    """Extra fileactions for vimiv."""

    def __init__(self, app):
        """Receive and set main vimiv application.

        Args:
            _app: The main vimiv class to interact with.
            _use_primary: True if operating on primary clipboard. Else clipboard
                is used.
        """
        self._app = app
        self._use_primary = self._app.settings["GENERAL"]["copy_to_primary"]

    def format_files(self, string):
        """Format image names in filelist according to a formatstring.

        Numbers files in form of formatstring_000.extension. Replaces exif
        information accordingly.

        Args:
            string: Formatstring to use.
        """
        # Catch problems
        if self._app["library"].is_focus():
            message = "Format only works on opened image files"
            self._app["statusbar"].message(message, "info")
            return
        if not self._app.get_paths():
            self._app["statusbar"].message("No files in path", "info")
            return

        # Check if exifdata is available and needed
        tofind = ("%" in string)
        if tofind:
            try:
                for fil in self._app.get_paths():
                    with Image.open(fil) as im:
                        # This will be removed once PIL is deprecated
                        # pylint: disable=protected-access
                        exif = im._getexif()
                        if not (exif and 306 in exif):
                            raise AttributeError
            except AttributeError:
                self._app["statusbar"].message(
                    "No exif data for %s available" % (fil), "error")
                return

        for i, fil in enumerate(self._app.get_paths()):
            ending = os.path.splitext(fil)[1]
            num = "%03d" % (i + 1)
            # Exif stuff
            if tofind:
                with Image.open(fil) as im:
                    # This will be removed once PIL is deprecated
                    # pylint: disable=protected-access
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

        self._app.emit("paths-changed", self)

    def copy_name(self, abspath=False):
        """Copy image name to clipboard.

        Args:
            abspath: Use absolute path or only the basename.
        """
        # Get name to copy
        name = self._app.get_pos(True)
        if abspath:
            name = os.path.abspath(name)
        else:
            name = os.path.basename(name)
        # Set clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY) \
            if self._use_primary \
            else Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        # Text to clipboard
        clipboard.set_text(name, -1)
        # Info message
        message = "Copied <b>" + name + "</b> to %s" % \
            ("primary" if self._use_primary else "clipboard")
        self._app["statusbar"].message(message, "info")

    def toggle_clipboard(self):
        """Toggle between primary and clipboard selection."""
        self._use_primary = not self._use_primary
