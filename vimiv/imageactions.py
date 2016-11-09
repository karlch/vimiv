#!/usr/bin/env python3
# encoding: utf-8
"""Actions which act on the actual image file."""
import os
from shutil import copyfile
from subprocess import Popen, PIPE
from threading import Thread
from PIL import Image, ImageEnhance
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk


def save_image(im, filename):
    """Save the image with all the exif keys that exist.

    Args:
        im: PIL image to act on.
        filename: Name of the image to save.
    """
    argstr = "filename"
    for key in im.info.keys():
        argstr += ", " + key + "=" + str(im.info[key])
    func = "im.save(" + argstr + ")"
    exec(func)


def rotate_file(filelist, cwise):
    """Rotate every image in filelist cwise*90° counterclockwise.

    Args:
        filelist: List of files to operate on.
        cwise: Rotation amount. Rotation is cwise*90° counterclockwise.
    """
    # Always work on realpath, not on symlink
    filelist = [os.path.realpath(image) for image in filelist]
    for image in filelist:
        with open(image, "rb") as image_file:
            im = Image.open(image_file)
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
        with open(image, "rb") as image_file:
            im = Image.open(image_file)
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
    # jhead does this better
    try:
        if method == "PIL":
            raise ValueError
        cmd = ["jhead", "-autorot", "-ft"] + filelist
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        out = out.decode(encoding='UTF-8')
        err = err.decode(encoding='UTF-8')
        # Find out how many images were rotated
        for line in out.split("\n"):
            if "Modified" in line and line.split()[1] not in err:
                rotated_images += 1
        # Added to the message displayed when done
        method = "jhead"
    # If it isn't there fall back to PIL
    except:
        for path in filelist:
            with open(path, "rb") as image_file:
                im = Image.open(image_file)
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


class Thumbnails:
    """Thumbnail creation class.

    Attributes:
        filelist: List of files to operate on.
        thumbsize: Size of thumbnails that are created.
        directory: Directory to save thumbnails in.
        thumbnails: Cached thumbnails that have been created already.
        thumblist: List of required thumbnails.
        thumbdict: Dictionary with required thumbnails and original filename.
        threads: Threads that are running for thumbnail creation.
    """

    def __init__(self, filelist, thumbsize):
        """Create default settings.

        Args:
            filelist: List of files to operate on.
            thumbsize: Size of thumbnails that are created.
        """
        self.filelist = filelist
        self.thumbsize = thumbsize
        self.directory = os.path.expanduser("~/.vimiv/Thumbnails")
        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)
        self.thumbnails = os.listdir(self.directory)
        self.thumblist = []  # List of all files with thumbnails
        self.thumbdict = {}  # Asserts thumbnails to their original file
        # Tuple containing all files for which thumbnail creation failed and
        # their position
        self.threads = []

    def thumbnails_create(self):
        """Create thumbnails for all images in filelist if they do not exist."""
        # Loop over all files
        for i, infile in enumerate(self.filelist):
            # Correct name
            thumb_ext = ".thumbnail_%dx%d" % (self.thumbsize[0],
                                              self.thumbsize[1])
            outfile_ext = infile.split(".")[0] + thumb_ext + ".png"
            outfile_base = os.path.basename(outfile_ext)
            outfile = os.path.join(self.directory, outfile_base)
            # Only if they aren't cached already
            if outfile_base not in self.thumbnails:
                thread_for_thumbnail = Thread(target=self.thread_for_thumbnails,
                                              args=(infile, outfile, i))
                self.threads.append(thread_for_thumbnail)
                thread_for_thumbnail.start()
            else:
                self.thumblist.append(outfile)
                self.thumbdict[outfile] = infile

        while self.threads:
            self.threads[0].join()
        self.thumblist.sort(
            key=lambda x: self.filelist.index(self.thumbdict[x]))
        return self.thumblist

    def thread_for_thumbnails(self, infile, outfile, position):
        """Create thumbnail in an extra thread.

        If thumbnail creation fails, defaults to the Adwaita dialog error.

        Args:
            infile: Image file to operate on.
            outfile: Name of thumbnail file to write to.
            position: Integer position of this thumbnail in the filelist.
        """
        try:
            with open(infile, "rb") as image_file:
                im = Image.open(image_file)
                im.thumbnail(self.thumbsize, Image.ANTIALIAS)
                save_image(im, outfile)
        except:
            icon_theme = Gtk.IconTheme.get_default()
            icon_info = icon_theme.lookup_icon("dialog-error", 256, 0)
            default_infile = icon_info.get_filename()
            copyfile(default_infile, outfile)
        self.thumblist.append(outfile)
        self.thumbdict[outfile] = infile
        self.threads.pop(0)


def manipulate_all(image, outfile, manipulations):
    """Apply all the manipulations to image.

    Manipulations include brightness, contrast and sharpness.

    Args:
        image: Name of the image to manipulate.
        outfile: File to save the manipulated image to.
        Manipulations: Values of manipulations to apply.

    Return: 1 for errors, 0 else.
    """
    if manipulations[3]:  # Optimize
        try:
            Popen(["mogrify", "-contrast", "-auto-gamma", "-auto-level",
                   image], shell=False).communicate()
        except:
            return 1
    # Enhance all three other values
    with open(image, "rb") as image_file:
        im = Image.open(image_file)
        im = ImageEnhance.Brightness(im).enhance(manipulations[0])
        im = ImageEnhance.Contrast(im).enhance(manipulations[1])
        im = ImageEnhance.Sharpness(im).enhance(manipulations[2])
        save_image(im, outfile)

    return 0
