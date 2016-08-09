#!/usr/bin/env python3
# encoding: utf-8
""" Actions which act on the actual image file """
import os
from subprocess import Popen, PIPE
from PIL import Image, ImageEnhance


def save_image(im, filename):
    """ Saves the PIL image name with all the keys that exist """
    argstr = "filename"
    for key in im.info.keys():
        argstr += ", " + key + "=" + str(im.info[key])
    func = "im.save(" + argstr + ")"
    exec(func)


def rotate_file(filelist, cwise):
    """ Rotate every image in filelist cwise*90° counterclockwise """
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
    """ Flips every image in filelist """
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
    """ This function autorotates all pictures in the current pathlist """
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


def thumbnails_create(filelist, thumbsize):
    """ Creates thumbnails for all images in filelist if they don't exist """
    # Create thumbnail directory if necessary
    thumbdir = os.path.expanduser("~/.vimiv/Thumbnails")
    if not os.path.isdir(thumbdir):
        os.mkdir(thumbdir)
    # Get all thumbnails that were already created
    thumbnails = os.listdir(thumbdir)
    thumblist = []  # List of all files with thumbnails
    errtuple = ([], [])    # Tuple containing all files for which thumbnail
    # creation failed and their position

    # Loop over all files
    for i, infile in enumerate(filelist):
        # Correct name
        outfile_ext = infile.split(".")[0] + ".thumbnail" + ".png"
        outfile_base = os.path.basename(outfile_ext)
        outfile = os.path.join(thumbdir, outfile_base)
        # Only if they aren't cached already
        if outfile_base not in thumbnails:
            try:
                with open(infile, "rb") as image_file:
                    im = Image.open(image_file)
                    im.thumbnail(thumbsize, Image.ANTIALIAS)
                    save_image(im, outfile)
                    thumblist.append(outfile)
            except:
                errtuple[0].append(i)
                errtuple[1].append(os.path.basename(infile))
        else:
            thumblist.append(outfile)

    return thumblist, errtuple


def manipulate_all(image, outfile, manipulations):
    """ Apply all the manipulations to image saving to outfile. These include
    optimize, brightness, contrast and sharpness. """
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
