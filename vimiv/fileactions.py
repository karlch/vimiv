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
            app: The main vimiv class to interact with.
            clipboard: Gtk Clipboard depending on config.
        """
        self.app = app
        self.use_primary = self.app.settings["GENERAL"]["copy_to_primary"]

    def format_files(self, string):
        """Format image names in filelist according to a formatstring.

        Numbers files in form of formatstring_000.extension. Replaces exif
        information accordingly.

        Args:
            string: Formatstring to use.
        """
        # Catch problems
        if self.app["library"].is_focus():
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
        # TODO delete this
        # Reload library remembering position
        if (directory == os.getcwd() and directory != self.app["tags"].directory
                and self.app["library"].grid.is_visible()):
            old_pos_lib = self.app.get_pos(False, "lib")
            if old_pos_lib >= 0 and \
                    old_pos_lib <= len(self.app["library"].files):
                self.app["library"].remember_pos(directory, old_pos_lib)
            self.app["library"].reload(directory)
            # Refocus other widgets if necessary
            if self.app["commandline"].last_focused == "im":
                self.app["image"].scrolled_win.grab_focus()
            elif self.app["commandline"].last_focused == "thu":
                self.app["thumbnail"].grab_focus()
        # Reload image/thumbnail
        if self.app.paths and reload_path:
            old_pos_im = self.app.get_pos(False, "im")
            # Get all files in directory again
            pathdir = os.path.dirname(self.app.paths[old_pos_im])
            files = [os.path.join(pathdir, fil)
                     for fil in sorted(os.listdir(pathdir))]
            self.app.paths, self.app.index = populate(files)
            # Expand library if set by user and all paths were removed
            if self.app["library"].expand and not self.app.paths:
                self.app["library"].set_hexpand(True)
            # Refocus the current position
            if self.app["thumbnail"].toggled:
                old_pos_thu = self.app.get_pos(False, "thu")
                for image in self.app.paths:
                    self.app["thumbnail"].reload(image)
                self.app["thumbnail"].move_to_pos(old_pos_thu)
            else:
                self.app["eventhandler"].num_str = str(old_pos_im + 1)
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
