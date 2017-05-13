# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Handle marking of images for vimiv."""

import os

from gi.repository import GObject


class Mark(GObject.Object):
    """Handle marking of images.

    Attributes:
        marked: List of currently marked images.

        _app: The main vimiv application to interact with.
        _marked_bak: List of last marked images to be able to toggle marks.
    """

    def __init__(self, app, settings):
        super(Mark, self).__init__()
        self._app = app
        self.marked = []
        self._marked_bak = []

    def mark(self):
        """Mark the current image."""
        # Check which image
        current = os.path.abspath(os.path.basename(self._app.get_pos(True)))
        # Toggle the mark
        if os.path.isfile(current):
            if current in self.marked:
                self.marked.remove(current)
            else:
                self.marked.append(current)
            self.emit("marks-changed", [current])
        else:
            self._app["statusbar"].message(
                "Marking directories is not supported", "warning")

    def toggle_mark(self):
        """Toggle mark status.

        If images are marked all marks are removed, otherwise the last marked
        images are re-marked.
        """
        if self.marked:
            self._marked_bak = self.marked
            self.marked = []
        else:
            self.marked, self._marked_bak = self._marked_bak, self.marked
        to_reload = self.marked + self._marked_bak
        self.emit("marks-changed", to_reload)

    def mark_all(self):
        """Mark all images."""
        # Get the correct filelist
        if self._app["library"].is_focus():
            files = []
            for fil in self._app["library"].files:
                files.append(os.path.abspath(fil))
        elif self._app.paths:
            files = self._app.paths
        else:
            self._app["statusbar"].message("No image to mark", "error")
        # Add all to the marks
        for fil in files:
            if os.path.isfile(fil) and fil not in self.marked:
                self.marked.append(fil)
        self.emit("marks-changed", files)

    def mark_between(self):
        """Mark all images between the two last marks."""
        # Check if there are enough marks
        if len(self.marked) < 2:
            self._app["statusbar"].message("Not enough marks", "error")
            return
        start = self.marked[-2]
        end = self.marked[-1]
        # Get the correct filelist
        if self._app["library"].is_focus():
            files = []
            for fil in self._app["library"].files:
                if not os.path.isdir(fil):
                    files.append(os.path.abspath(fil))
        elif self._app.paths:
            files = self._app.paths
        else:
            self._app["statusbar"].message("No image to mark", "error")
        # Find the images to mark
        for i, image in enumerate(files):
            if image == start:
                start = i
            elif image == end:
                end = i
        for i in range(start + 1, end):
            self.marked.insert(-1, files[i])
        self.emit("marks-changed", self.marked)


GObject.signal_new("marks-changed", Mark, GObject.SIGNAL_RUN_LAST, None,
                   (GObject.TYPE_PYOBJECT,))
