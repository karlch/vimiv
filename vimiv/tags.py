#!/usr/bin/env python
# encoding: utf-8
"""Deal with the handling of tags for vimiv."""
import os
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
from vimiv.helpers import read_file
from vimiv.fileactions import populate


class TagHandler(object):
    """Handle tags.

    Attributes:
        vimiv: The main vimiv class to interact with.
        directory: Directory in which tags are stored.
        last: Last tag that was loaded.
    """

    def __init__(self, vimiv):
        """Create the necessary objects.

        Args:
            vimiv: The main vimiv class to interact with.
        """
        self.vimiv = vimiv
        self.directory = os.path.join(self.vimiv.directory, "Tags")
        self.last = ""

    def read(self, tagname):
        """Read a tag and return the images in it.

        Args:
            tagname: Name of tag to operate on.

        Return: List of images in the tag called tagname.
        """
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = read_file(tagfile_name)
        return tagged_images

    def write(self, imagelist, tagname):
        """Add a list of images to a tag.

        Args:
            imagelist: List of images to write to the tag.
            tagname: Name of tag to operate on.
        """
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = self.read(tagname)

        with open(tagfile_name, 'a') as tagfile:
            for image in imagelist:
                if image not in tagged_images:
                    tagfile.write(image + "\n")

    def remove(self, tagname):
        """Remove a tag showing an error if the tag doesn't exist.

        Args:
            tagname: Name of tag to operate on.
        """
        tagfile_name = os.path.join(self.directory, tagname)
        if os.path.isfile(tagfile_name):
            os.remove(tagfile_name)
        else:
            err = "Tagfile '%s' does not exist" % (tagname)
            self.vimiv.statusbar.err_message(err)

    def load(self, tagname):
        """Load all images in a tag as current filelist.

        Args:
            tagname: Name of tag to operate on.
        """
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
                self.vimiv.library.scrollable_treeview.set_size_request(
                    self.vimiv.library.width, 10)
                # Find out tag position
                # self.vimiv.library.remember_pos(self.directory, 2)
                self.vimiv.library.reload(self.directory)
                tag_pos = self.vimiv.library.files.index(tagname)
                self.vimiv.library.treeview.set_cursor(Gtk.TreePath(tag_pos),
                                                       None, False)
                self.vimiv.library.treepos = tag_pos
        else:
            message = "Tagfile '%s' has no valid images" % (tagname)
            self.vimiv.statusbar.err_message(message)
