#!/usr/bin/env python
# encoding: utf-8
"""Handle marking of images for vimiv."""

import os


class Mark(object):
    """Handle marking of images.

    Attributes:
        app: The main vimiv application to interact with.
        marked: List of currently marked images.
        marked_bak: List of last marked images to be able to toggle mark status.
    """

    def __init__(self, app, settings):
        self.app = app
        self.marked = []
        self.marked_bak = []

    def mark(self):
        """Mark the current image."""
        # Check which image
        if self.app["library"].treeview.is_focus():
            current = os.path.abspath(self.app.get_pos(True))
        elif self.app["thumbnail"].toggled:
            index = self.app.get_pos()
            current = self.app.paths[index]
        else:
            current = self.app.paths[self.app.index]
        # Toggle the mark
        if os.path.isfile(current):
            if current in self.marked:
                self.marked.remove(current)
            else:
                self.marked.append(current)
            self.mark_reload(False, [current])
        else:
            self.app["statusbar"].err_message(
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
        if self.app["library"].treeview.is_focus():
            files = []
            for fil in self.app["library"].files:
                files.append(os.path.abspath(fil))
        elif self.app.paths:
            files = self.app.paths
        else:
            self.app["statusbar"].err_message("No image to mark")
        # Add all to the marks
        for fil in files:
            if os.path.isfile(fil) and fil not in self.marked:
                self.marked.append(fil)
        self.mark_reload()

    def mark_between(self):
        """Mark all images between the two last marks."""
        # Check if there are enough marks
        if len(self.marked) < 2:
            self.app["statusbar"].err_message("Not enough marks")
            return
        start = self.marked[-2]
        end = self.marked[-1]
        # Get the correct filelist
        if self.app["library"].treeview.is_focus():
            files = []
            for fil in self.app["library"].files:
                if not os.path.isdir(fil):
                    files.append(os.path.abspath(fil))
        elif self.app.paths:
            files = self.app.paths
        else:
            self.app["statusbar"].err_message("No image to mark")
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
        if self.app["library"].grid.is_visible():
            self.app["library"].remember_pos(os.getcwd(), self.app.get_pos())
            self.app["library"].reload(os.getcwd())
        if self.app["thumbnail"].toggled:
            for i, image in enumerate(self.app.paths):
                if reload_all or image in current:
                    self.app["thumbnail"].reload(image, i, False)

        self.app["statusbar"].update_info()
