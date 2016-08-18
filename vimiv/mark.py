#!/usr/bin/env python
# encoding: utf-8
"""Handle marking of images for vimiv."""

import os


class Mark(object):
    """Handle marking of images.

    Attributes:
        vimiv: The main vimiv class to interact with.
        marked: List of currently marked images.
        marked_bak: List of last marked images to be able to toggle mark status.
    """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        self.marked = []
        self.marked_bak = []

    def mark(self):
        """Mark the current image."""
        # Check which image
        if self.vimiv.library.treeview.is_focus():
            current = os.path.abspath(self.vimiv.library.files[
                self.vimiv.library.get_treepos()])
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
        """Toggle mark status.

        If images are marked all marks are removed, otherwise the last marked
        images are re-marked.
        """
        if self.marked:
            self.marked_bak = self.marked
            self.marked = []
        else:
            self.marked, self.marked_bak = self.marked_bak, self.marked
        to_reload = self.marked + self.marked_bak
        self.mark_reload(False, to_reload)

    def mark_all(self):
        """Mark all images."""
        # Get the correct filelist
        if self.vimiv.library.treeview.is_focus():
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
        """Mark all images between the two last marks."""
        # Check if there are enough marks
        if len(self.marked) < 2:
            self.vimiv.statusbar.err_message("Not enough marks")
            return
        start = self.marked[-2]
        end = self.marked[-1]
        # Get the correct filelist
        if self.vimiv.library.treeview.is_focus():
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
        """Reload all information which contains marks."""
        # Update lib
        if self.vimiv.library.toggled:
            self.vimiv.library.remember_pos(os.getcwd(),
                                            self.vimiv.library.get_treepos())
            self.vimiv.library.reload(os.getcwd())
        if self.vimiv.thumbnail.toggled:
            for i, image in enumerate(self.vimiv.paths):
                if reload_all or image in current:
                    self.vimiv.thumbnail.reload(image, i, False)

        self.vimiv.statusbar.update_info()
