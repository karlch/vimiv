# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Actions which act on the actual image file."""

import os
from shutil import which
from subprocess import PIPE, Popen

from gi.repository import GdkPixbuf

try:
    from gi.repository import GExiv2
    _has_exif = True
except ImportError:
    _has_exif = False


def save_pixbuf(pixbuf, filename):
    """Save the image with all the exif keys that exist if we have exif support.

    NOTE: This is used to override edited images, not to save images to new
        paths. The filename must exist as it is used to retrieve the image
        format and exif data.

    Args:
        pixbuf: GdkPixbuf.Pixbuf image to act on.
        filename: Name of the image to save.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError("Original file to retrieve data from not found")
    # Get needed information
    info = GdkPixbuf.Pixbuf.get_file_info(filename)[0]
    extension = info.get_extensions()[0]
    if _has_exif:
        exif = GExiv2.Metadata(filename)
    # Save
    pixbuf.savev(filename, extension, [], [])
    if _has_exif:
        exif.save_file()


def rotate_file(filename, cwise):
    """Rotate a file and save it.

    Args:
        filename: Name of the image to rotate.
        cwise: Rotate image 90 * cwise degrees.
    """
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    pixbuf = pixbuf.rotate_simple(90 * cwise)
    save_pixbuf(pixbuf, filename)


def flip_file(filename, horizontal):
    """Flip a file and save it.

    Args:
        filename: Name of the image to flip.
        horizontal: If True, flip horizontally. Else vertically.
    """
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    pixbuf = pixbuf.flip(horizontal)
    save_pixbuf(pixbuf, filename)


def autorotate(filelist, method="auto"):
    """Autorotate all pictures in filelist according to exif information.

    Args:
        filelist: List of files to operate on.
        method: Method to use. Auto tries jhead and falls back to PIL.
    """
    rotated_images = 0
    # Check for which method in auto
    if method == "auto":
        method = "jhead" if which("jhead") else "PIL"
    # jhead does this better
    if method == "jhead":
        cmd = ["jhead", "-autorot", "-ft"] + filelist
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        out = out.decode(encoding="UTF-8")
        err = err.decode(encoding="UTF-8")
        # Find out how many images were rotated
        for line in out.split("\n"):
            if "Modified" in line and line.split()[1] not in err:
                rotated_images += 1
        # Added to the message displayed when done
        method = "jhead"
    elif method == "PIL":
        # TODO
        return

    # Return the amount of rotated images and the method used
    return rotated_images, method
