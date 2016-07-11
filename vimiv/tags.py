#!/usr/bin/env python
# encoding: utf-8
""" Deals with the handling of tags for vimiv """
import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv.helpers import read_file
from vimiv.fileactions import populate

class TagHandler(object):
    """ Handles tags """

    def __init__(self, vimiv):
        self.vimiv = vimiv
        self.directory = os.path.join(self.vimiv.directory, "Tags")
        self.last = ""

    def read(self, tagname):
        """ Returns a list of all images in tagname """
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = read_file(tagfile_name)
        return tagged_images

    def write(self, imagelist, tagname):
        """ Adds the images in imagelist to the tag named tagname """
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = self.read(tagname)

        with open(tagfile_name, 'a') as tagfile:
            for image in imagelist:
                if image not in tagged_images:
                    tagfile.write(image + "\n")

    def remove(self, tagname):
        """ Remove tagname showing an error if the tag doesn't exist """
        tagfile_name = os.path.join(self.directory, tagname)
        if os.path.isfile(tagfile_name):
            os.remove(tagfile_name)
        else:
            err = "Tagfile '%s' does not exist" % (tagfile_name)
            self.vimiv.statusbar.err_message(err)

    def load(self, tagname):
        """ Load all images in tag 'name' as current filelist """
        os.chdir(self.directory)
        # Read file and get all tagged images as list
        tagged_images = self.read(tagname)
        # Populate filelist
        self.vimiv.paths = []
        self.vimiv.paths = populate(tagged_images)[0]
        if self.vimiv.paths:
            self.vimiv.image.scrolled_win.show()
            self.vimiv.image.move_index(False, False, 0)
            # Focus in library if it is open
            if self.vimiv.library.toggled:
                self.vimiv.library.grid.set_size_request(self.vimiv.library.width
                                                 -self.vimiv.library.border_width, 10)
                # Find out tag position
                # self.vimiv.library.remember_pos(self.directory, 2)
                self.vimiv.library.reload(self.directory)
                tag_pos = self.vimiv.library.files.index(tagname)
                self.vimiv.library.treeview.set_cursor(Gtk.TreePath(tag_pos),
                                                       None, False)
                self.vimiv.library.treepos = tag_pos
        else:
            err = "Tagfile '%s' has no valid images" % (tagname)
            self.vimiv.statusbar.err_message(err)
