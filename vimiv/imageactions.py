# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Actions which act on the actual image file."""

import os
from shutil import which
from subprocess import PIPE, Popen

from PIL import Image


def save_image(im, filename):
    """Save the image with all the exif keys that exist.

    Args:
        im: PIL image to act on.
        filename: Name of the image to save.
    """
    kwargs = im.info
    im.save(filename, **kwargs)


def rotate_file(filelist, cwise):
    """Rotate every image in filelist cwise*90° counterclockwise.

    Args:
        filelist: List of files to operate on.
        cwise: Rotation amount. Rotation is cwise*90° counterclockwise.
    """
    # Always work on realpath, not on symlink
    filelist = [os.path.realpath(image) for image in filelist]
    for image in filelist:
        with Image.open(image) as im:
            if cwise == 1:
                im = im.transpose(Image.ROTATE_90)
            elif cwise == 2:
                im = im.transpose(Image.ROTATE_180)
            elif cwise == 3:
                im = im.transpose(Image.ROTATE_270)
            save_image(im, image)


def flip_file(filelist, horizontal):
    """Flip every image in the correct direction.

    Args:
        filelist: List of files to operate on.
        horizontal: If True, flip horizontally. Else flip vertically.
    """
    # Always work on realpath, not on symlink
    filelist = [os.path.realpath(image) for image in filelist]
    for image in filelist:
        with Image.open(image) as im:
            if horizontal:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            save_image(im, image)


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
        for path in filelist:
            with Image.open(path) as im:
                exif = im._getexif()
                orientation_key = 274  # cf ExifTags
                rotated = True

                # Only do something if orientation info is there
                if exif and orientation_key in exif:
                    orientation = exif[orientation_key]
                    # Rotate and save the image
                    if orientation == 3:
                        im = im.transpose(Image.ROTATE_180)
                    elif orientation == 6:
                        im = im.transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        im = im.transpose(Image.ROTATE_90)
                    else:
                        rotated = False
                    if rotated:
                        save_image(im, path)
                        rotated_images += 1
            method = "PIL"

    # Return the amount of rotated images and the method used
    return rotated_images, method
