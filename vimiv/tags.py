#!/usr/bin/env python
# encoding: utf-8
""" Deals with the handling of tags for vimiv """
import os
from vimiv.helpers import read_file

# Directories
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
trashdir = os.path.join(vimivdir, "Trash")
tagdir = os.path.join(vimivdir, "Tags")

def tag_read(tagname):
    """ Returns a list of all images in tagname """
    tagfile_name = os.path.join(tagdir, tagname)
    tagged_images = read_file(tagfile_name)
    return tagged_images

def tag_write(imagelist, tagname):
    """ Adds the images in imagelist to the tag named tagname """
    tagfile_name = os.path.join(tagdir, tagname)
    tagged_images = tag_read(tagname)

    with open(tagfile_name, 'a') as tagfile:
        for image in imagelist:
            if image not in tagged_images:
                tagfile.write(image + "\n")

def tag_remove(tagname):
    tagfile_name = os.path.join(tagdir, tagname)
    if os.path.isfile(tagfile_name):
        os.remove(tagfile_name)
    else:
        pass # TODO an error
