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
    for image in filelist:
        im = Image.open(image)
        if cwise == 1:
            im = im.transpose(Image.ROTATE_90)
        elif cwise == 2:
            im = im.transpose(Image.ROTATE_180)
        elif cwise == 3:
            im = im.transpose(Image.ROTATE_270)
        save_image(im, image)


def flip_file(filelist, horizontal):
    """ Flips every image in filelist """
    for image in filelist:
        im = Image.open(image)
        if horizontal:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        else:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        save_image(im, image)


def autorotate(filelist):
    """ This function autorotates all pictures in the current pathlist """
    rotated_images = 0
    # jhead does this better
    try:
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
            im = Image.open(path)
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


def thumbnails_create(filelist , thumbsize):
    """ Creates thumbnails for all images in filelist if they don't exist """
    # Create thumbnail directory if necessary
    thumbdir = os.path.expanduser("~/.vimiv/Thumbnails")
    if not os.path.isdir(thumbdir):
        os.mkdir(thumbdir)
    # Get all thumbnails that were already created
    thumbnails = os.listdir(thumbdir)
    thumblist = []  # List of all files with thumbnails
    errlist = []    # List of all files for which thumbnail creation failed

    # Loop over all files
    for i, infile in enumerate(filelist):
        # Correct name
        outfile = ".".join(infile.split(".")[:-1]) + ".thumbnail" + ".png"
        outfile = outfile.split("/")[-1]
        outfile = os.path.join(thumbdir, outfile)
        # Only if they aren't cached already
        if outfile.split("/")[-1] not in thumbnails:
            try:
                im = Image.open(infile)
                im.thumbnail(thumbsize, Image.ANTIALIAS)
                save_image(im, outfile)
                thumblist.append(outfile)
            except:
                errlist.append([i, infile])
        else:
            thumblist.append(outfile)

    return thumblist, errlist


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
    im = Image.open(image)
    im = ImageEnhance.Brightness(im).enhance(manipulations[0])
    im = ImageEnhance.Contrast(im).enhance(manipulations[1])
    im = ImageEnhance.Sharpness(im).enhance(manipulations[2])
    # Write
    save_image(im, outfile)

    return 0
