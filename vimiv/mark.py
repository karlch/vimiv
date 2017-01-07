#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
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
        current = os.path.abspath(os.path.basename(self.app.get_pos(True)))
        # Toggle the mark
        if os.path.isfile(current):
            if current in self.marked:
                self.marked.remove(current)
            else:
                self.marked.append(current)
            self.mark_reload(False, [current])
        else:
            self.app["statusbar"].message(
                "Marking directories is not supported", "warning")

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
            self.app["statusbar"].message("No image to mark", "error")
        # Add all to the marks
        for fil in files:
            if os.path.isfile(fil) and fil not in self.marked:
                self.marked.append(fil)
        self.mark_reload()

    def mark_between(self):
        """Mark all images between the two last marks."""
        # Check if there are enough marks
        if len(self.marked) < 2:
            self.app["statusbar"].message("Not enough marks", "error")
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
            self.app["statusbar"].message("No image to mark", "error")
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
            model = self.app["library"].treeview.get_model()
            for i, name in enumerate(self.app["library"].files):
                model[i][3] = "[*]" \
                    if os.path.abspath(name) in self.marked \
                    else ""
        # Reload thumb names
        if self.app["thumbnail"].toggled:
            reload_list = self.app.paths if reload_all else current
            for image in reload_list:
                self.app["thumbnail"].reload(image, False)

        self.app["statusbar"].update_info()
