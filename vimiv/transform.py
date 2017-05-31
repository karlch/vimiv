# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Deals with transformations like rotate and flip and deleting files."""

import os

from threading import Thread

from gi.repository import GObject
from vimiv import imageactions
from vimiv.fileactions import is_animation
from vimiv.trash_manager import TrashManager


class Transform(GObject.Object):
    """Deals with transformations like rotate/flip and deleting files.

    Attributes:
        threads_running: If True, a thread is running to apply to files.
        trash_manager: Class to handle a shared trash directory.

        _app: The main vimiv application to interact with.
        _changes: Dictionary for rotate and flip.
            Key: Filename; Item: [Int, Bool, Bool]

    Signals:
        changed: Emitted when an image was transformed so Image can update.
        applied-to-file: Emitted when the file was successfully transformed.
    """

    def __init__(self, app):
        super(Transform, self).__init__()
        self._app = app
        self._changes = {}
        self.trash_manager = TrashManager()
        self.threads_running = False

    def delete(self):
        """Delete all marked images or the current one."""
        # Get all images
        images = self.get_images("Deleted")
        self._app["mark"].marked = []
        # Delete all images remembering possible errors
        message = ""
        for im in images:
            if not os.path.exists(im):
                message += "Image %s does not exist." % (im)
            elif os.path.isdir(im):
                message += "Deleting directory %s is not supported." % (im)
            else:
                self.trash_manager.delete(im)
        if message:
            self._app["statusbar"].message(message, "error")

        self._app.emit("paths-changed", self)

    def undelete(self, basename):
        """Undelete an image in the trash.

        Args:
            basename: The basename of the image in the trash directory.
        """
        returncode = self.trash_manager.undelete(basename)
        if returncode == 1:
            message = "Could not restore %s, file does not exist" % (basename)
            self._app["statusbar"].message(message, "error")
        elif returncode == 2:
            message = "Could not restore %s, directories are not supported" \
                % (basename)
            self._app["statusbar"].message(message, "error")
        elif returncode == 3:
            message = "Could not restore %s, directory is not accessible" \
                % (basename)
            self._app["statusbar"].message(message, "error")
        else:
            self._app.emit("paths-changed", self)

    def get_images(self, info):
        """Return the images which should be manipulated.

        Either the currently focused image or all marked images.

        Args:
            info: Info to display when acting on marked images.
        """
        # Add all marked images
        if self._app["mark"].marked:
            images = self._app["mark"].marked
            if len(images) == 1:
                message = "%s %d marked image" % (info, len(images))
            else:
                message = "%s %d marked images" % (info, len(images))
            self._app["statusbar"].message(message, "info")
        # Add the image shown
        else:
            images = [os.path.abspath(self._app.get_pos(True))]
        return images

    def rotate(self, cwise):
        """Rotate the displayed image and call thread to rotate files.

        Args:
            cwise: Rotate image 90 * cwise degrees.
        """
        if not self._app.get_paths():
            self._app["statusbar"].message(
                "No image to rotate", "error")
            return
        # Do not rotate animations
        elif is_animation(self._app.get_path()):
            self._app["statusbar"].message(
                "Animations cannot be rotated", "warning")
            return
        try:
            cwise = int(cwise)
            images = self.get_images("Rotated")
            cwise = cwise % 4
            # Update properties
            for fil in images:
                if fil in self._changes:
                    self._changes[fil][0] = \
                        (self._changes[fil][0] + cwise) % 4
                else:
                    self._changes[fil] = [cwise, 0, 0]
            # Rotate the image shown
            if self._app.get_path() in images:
                self.emit("changed", "rotate", cwise)
            # Reload thumbnails of rotated images immediately
            if self._app["thumbnail"].toggled:
                self.apply()
        except ValueError:
            self._app["statusbar"].message(
                "Argument for rotate must be of type integer", "error")

    def apply(self):
        """Start thread for rotate and flip."""
        # TODO improve this, it is currently not possible to find out what is
        # being changed and what should still be done
        if self.threads_running:
            return
        t = Thread(target=self._thread_for_apply)
        t.start()

    def _thread_for_apply(self):
        """Rotate and flip image file in an extra thread."""
        self.threads_running = True
        to_remove = list(self._changes.keys())
        for f in self._changes:
            if self._changes[f][0]:
                imageactions.rotate_file(f, self._changes[f][0])
            if self._changes[f][1]:
                imageactions.flip_file(f, True)
            if self._changes[f][2]:
                imageactions.flip_file(f, False)
        for key in to_remove:
            del self._changes[key]
        self.emit("applied-to-file", to_remove)
        self.threads_running = False

    def flip(self, horizontal):
        """Flip the displayed image and call thread to flip files.

        Args:
            horizontal: If True, flip horizontally. Else vertically.
        """
        if not self._app.get_paths():
            self._app["statusbar"].message(
                "No image to flip", "error")
            return
        # Do not flip animations
        elif is_animation(self._app.get_path()):
            self._app["statusbar"].message(
                "Animations cannot be flipped", "warning")
            return
        try:
            horizontal = int(horizontal)
            images = self.get_images("Flipped")
            # Apply changes
            for fil in images:
                if fil not in self._changes:
                    self._changes[fil] = [0, 0, 0]
                if horizontal:
                    self._changes[fil][1] = \
                        (self._changes[fil][1] + 1) % 2
                else:
                    self._changes[fil][2] = \
                        (self._changes[fil][2] + 1) % 2
            # Flip the image shown
            if self._app.get_path() in images:
                self.emit("changed", "flip", horizontal)
            # Reload thumbnails of flipped images immediately
            if self._app["thumbnail"].toggled:
                self.apply()
        except ValueError:
            self._app["statusbar"].message(
                "Argument for flip must be of type integer", "error")

    def rotate_auto(self):
        """Autorotate all pictures in the current pathlist."""
        autorotate = imageactions.Autorotate(self._app.get_paths())
        self.threads_running = True
        autorotate.connect("completed", self._on_autorotate_completed)
        autorotate.run()

    def _on_autorotate_completed(self, autorotate, amount):
        message = "Completed autorotate for %d files" % (amount)
        self.threads_running = False
        self._app["statusbar"].message(message, "info")


GObject.signal_new("changed", Transform, GObject.SIGNAL_RUN_LAST, None,
                   (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT))
GObject.signal_new("applied-to-file", Transform, GObject.SIGNAL_RUN_LAST, None,
                   (GObject.TYPE_PYOBJECT,))
