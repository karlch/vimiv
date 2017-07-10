# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Provides class to handle a shared trash directory.

The TrashManager deletes and undeletes images from the user's Trash directory in
$XDG_DATA_HOME/Trash according to the freedesktop.org trash specification.
"""

import configparser
import os
import shutil
import tempfile
import time

from gi.repository import GLib

from vimiv.exceptions import TrashUndeleteError


class TrashManager():
    """Provides mechanism to delete and undelete images.

    Attributes:
        files_directory: Directory to which the "deleted" files are moved.
        info_directory: Directory in which information on the "deleted" files is
            stored.
    """

    def __init__(self):
        """Create a new TrashManager."""
        self.files_directory = os.path.join(GLib.get_user_data_dir(),
                                            "Trash/files")
        self.info_directory = os.path.join(GLib.get_user_data_dir(),
                                           "Trash/info")
        os.makedirs(self.files_directory, exist_ok=True)
        os.makedirs(self.info_directory, exist_ok=True)

    def delete(self, filename):
        """Move a file to the trash directory.

        Args:
            filename: The original name of the file.
        """
        trash_filename = self._get_trash_filename(filename)
        self._create_info_file(trash_filename, filename)
        shutil.move(filename, trash_filename)

    def undelete(self, basename):
        """Undelete a file from the trash directory.

        Args:
            basename: The basename of the file in the trash directory.
        """
        info_filename = os.path.join(self.info_directory,
                                     basename + ".trashinfo")
        trash_filename = os.path.join(self.files_directory, basename)
        if not os.path.exists(info_filename) \
                or not os.path.exists(trash_filename):
            raise TrashUndeleteError("file does not exist")
        if os.path.isdir(trash_filename):
            raise TrashUndeleteError("directories are not supported")
        info = configparser.ConfigParser()
        info.read(info_filename)
        content = info["Trash Info"]
        original_filename = content["Path"]
        # Directory of the file is not accessible
        if not os.path.isdir(os.path.dirname(original_filename)):
            raise TrashUndeleteError("original directory is not accessible")
        shutil.move(trash_filename, original_filename)
        os.remove(info_filename)

    def _get_trash_filename(self, filename):
        """Return the name of the file in self.files_directory.

        Args:
            filename: The original name of the file.
        """
        path = os.path.join(self.files_directory, os.path.basename(filename))
        # Ensure that we do not overwrite any files
        extension = 2
        original_path = path
        while os.path.exists(path):
            path = original_path + "." + str(extension)
            extension += 1
        return path

    def _create_info_file(self, trash_filename, original_filename):
        """Create file with information as specified by the standard.

        Args:
            trash_filename: The name of the file in self.files_directory.
            original_filename: The original name of the file.
        """
        # Note: we cannot use configparser here as it writes keys in lowercase
        info_path = os.path.join(
            self.info_directory,
            os.path.basename(trash_filename) + ".trashinfo")
        # Write to temporary file and use shutil.move to make sure the operation
        # is an atomic operation as specified by the standard
        fd, temp_path = tempfile.mkstemp(dir=self.info_directory)
        os.close(fd)
        temp_file = open(temp_path, "w")
        temp_file.write("[Trash Info]\n")
        temp_file.write("Path=%s\n" % (original_filename))
        temp_file.write("DeletionDate=%s\n" % (time.strftime("%Y%m%dT%H%M%S")))
        # Make sure that all data is on disk
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        shutil.move(temp_path, info_path)

    def get_files_directory(self):
        return self.files_directory

    def get_info_directory(self):
        return self.info_directory
