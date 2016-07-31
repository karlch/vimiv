#!/usr/bin/env python
# encoding: utf-8
""" Handles marking of images for vimiv """

import os


class Mark(object):
    """ Handles marking of images """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        self.marked = []
        self.marked_bak = []  # saves marked images after marked toggle

    def mark(self):
        """ Marks the current image """
        # Check which image
        if self.vimiv.library.focused:
            current = os.path.abspath(self.vimiv.library.files[
                self.vimiv.library.treepos])
        elif self.vimiv.thumbnail.toggled:
            index = self.vimiv.thumbnail.pos
            pathindex = index
            # Remove errors and reload the thumb_name
            for i in self.vimiv.thumbnail.errorpos:
                if pathindex >= i:
                    pathindex += 1
            current = self.vimiv.paths[pathindex]
        else:
            current = self.vimiv.paths[self.vimiv.index]
        # Toggle the mark
        if os.path.isfile(current):
            if current in self.marked:
                self.marked.remove(current)
            else:
                self.marked.append(current)
            self.mark_reload(False, [current])
        else:
            self.vimiv.statusbar.err_message(
                "Marking directories is not supported")

    def toggle_mark(self):
        """ Toggles mark status: if images are marked all marks are removed,
            otherwise the last marked images are re-marked """
        if self.marked:
            self.marked_bak = self.marked
            self.marked = []
        else:
            self.marked, self.marked_bak = self.marked_bak, self.marked
        to_reload = self.marked + self.marked_bak
        self.mark_reload(False, to_reload)

    def mark_all(self):
        """ Marks all images """
        # Get the correct filelist
        if self.vimiv.library.focused:
            files = []
            for fil in self.vimiv.library.files:
                files.append(os.path.abspath(fil))
        elif self.vimiv.paths:
            files = self.vimiv.paths
        else:
            self.vimiv.statusbar.err_message("No image to mark")
        # Add all to the marks
        for fil in files:
            if os.path.isfile(fil) and fil not in self.marked:
                self.marked.append(fil)
        self.mark_reload()

    def mark_between(self):
        """ Marks all images between the two last selections """
        # Check if there are enough marks
        if len(self.marked) < 2:
            self.vimiv.statusbar.err_message("Not enough marks")
            return
        start = self.marked[-2]
        end = self.marked[-1]
        # Get the correct filelist
        if self.vimiv.library.focused:
            files = []
            for fil in self.vimiv.library.files:
                if not os.path.isdir(fil):
                    files.append(os.path.abspath(fil))
        elif self.vimiv.paths:
            files = self.vimiv.paths
        else:
            self.vimiv.statusbar.err_message("No image to mark")
        # Find the images to mark
        for i, image in enumerate(files):
            if image == start:
                start = i
            elif image == end:
                end = i
        for i in range(start + 1, end):
            self.marked.insert(-1, files[i])
        self.mark_reload()

    def mark_reload(self, reload_all=True, current=None):
        """ Reload all information which contains marks """
        # Update lib
        if self.vimiv.library.toggled:
            self.vimiv.library.remember_pos(".", self.vimiv.library.treepos)
            self.vimiv.library.reload(".")
        if self.vimiv.thumbnail.toggled:
            for i, image in enumerate(self.vimiv.paths):
                if reload_all or image in current:
                    self.vimiv.thumbnail.reload(image, i, False)

        self.vimiv.statusbar.update_info()
