#!/usr/bin/env python
# encoding: utf-8
""" Deals with the handling of tags for vimiv """
import os
from vimiv.helpers import read_file
from vimiv.fileactions import populate

# Directories
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
trashdir = os.path.join(vimivdir, "Trash")
tagdir = os.path.join(vimivdir, "Tags")

class TagHandler(object):
    """ Handles tags """

    def __init__(self, vimiv):
        self.vimiv = vimiv

    def tag_read(self, tagname):
        """ Returns a list of all images in tagname """
        tagfile_name = os.path.join(tagdir, tagname)
        tagged_images = read_file(tagfile_name)
        return tagged_images

    def tag_write(self, imagelist, tagname):
        """ Adds the images in imagelist to the tag named tagname """
        tagfile_name = os.path.join(tagdir, tagname)
        tagged_images = self.tag_read(tagname)

        with open(tagfile_name, 'a') as tagfile:
            for image in imagelist:
                if image not in tagged_images:
                    tagfile.write(image + "\n")

    def tag_remove(self, tagname):
        """ Remove tagname showing an error if the tag doesn't exist """
        tagfile_name = os.path.join(tagdir, tagname)
        if os.path.isfile(tagfile_name):
            os.remove(tagfile_name)
        else:
            err = "Tagfile '%s' does not exist" % (tagfile_name)
            self.vimiv.err_message(err)

    def tag_load(self, tagname):
        """ Load all images in tag 'name' as current filelist """
        os.chdir(tagdir)
        # Read file and get all tagged images as list
        tagged_images = self.tag_read(tagname)
        # Populate filelist
        self.vimiv.paths = []
        self.vimiv.paths = populate(tagged_images)[0]
        if self.vimiv.paths:
            self.vimiv.scrolled_win.show()
            self.vimiv.move_index(False, False, 0)
            # Close library if necessary
            if self.vimiv.library_toggled:
                self.vimiv.grid.set_size_request(self.vimiv.library_width
                                                 -self.vimiv.border_width, 10)
                self.vimiv.toggle_library()
        else:
            err = "Tagfile '%s' has no valid images" % (tagname)
            self.vimiv.err_message(err)
