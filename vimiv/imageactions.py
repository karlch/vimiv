# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Actions which act on the actual image file."""

import os
from multiprocessing.pool import ThreadPool as Pool

from gi.repository import GdkPixbuf, GObject

try:
    from gi.repository import GExiv2
    _has_exif = True
except ImportError:
    _has_exif = False


def save_pixbuf(pixbuf, filename):
    """Save the image with all the exif keys that exist if we have exif support.

    NOTE: This is used to override edited images, not to save images to new
        paths. The filename must exist as it is used to retrieve the image
        format and exif data.

    Args:
        pixbuf: GdkPixbuf.Pixbuf image to act on.
        filename: Name of the image to save.
    """
    if not os.path.isfile(filename):
        raise FileNotFoundError("Original file to retrieve data from not found")
    # Get needed information
    info = GdkPixbuf.Pixbuf.get_file_info(filename)[0]
    extension = info.get_extensions()[0]
    if _has_exif:
        exif = GExiv2.Metadata(filename)
    # Save
    pixbuf.savev(filename, extension, [], [])
    if _has_exif:
        exif.save_file()


def rotate_file(filename, cwise):
    """Rotate a file and save it.

    Args:
        filename: Name of the image to rotate.
        cwise: Rotate image 90 * cwise degrees.
    """
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    pixbuf = pixbuf.rotate_simple(90 * cwise)
    save_pixbuf(pixbuf, filename)


def flip_file(filename, horizontal):
    """Flip a file and save it.

    Args:
        filename: Name of the image to flip.
        horizontal: If True, flip horizontally. Else vertically.
    """
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    pixbuf = pixbuf.flip(horizontal)
    save_pixbuf(pixbuf, filename)


class Autorotate(GObject.Object):
    """Class to rotate a list of images according to EXIF in a thread pool.

    Attributes:
        _filelist: List of files to rotate.
        _rotated_count: Int to count the amount of files that have been rotated.
        _thread_pool: ThreadPool to use when rotating all images.

    Signals:
        completed: Emitted when all files where rotated so the statusbar can
            update.
    """

    def __init__(self, filelist):
        super(Autorotate, self).__init__()
        self._filelist = filelist
        self._rotated_count = 0

        _cpu_count = os.cpu_count()
        if _cpu_count is None:
            _cpu_count = 1
        elif _cpu_count > 1:
            _cpu_count -= 1
        self._thread_pool = Pool(_cpu_count)

    def run(self):
        """Start autorotating the images in self._filelist."""
        for filename in self._filelist:
            self._thread_pool.apply_async(self._rotate, (filename,),
                                          callback=self._on_rotated)

    def _rotate(self, filename):
        """Rotate filename using pixbuf.apply_embedded_orientation()."""
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        pixbuf = pixbuf.apply_embedded_orientation()
        save_pixbuf(pixbuf, filename)

    def _on_rotated(self, thread_pool_result):
        self._rotated_count += 1
        if self._rotated_count == len(self._filelist):
            self.emit("completed", self._rotated_count)


GObject.signal_new("completed", Autorotate, GObject.SIGNAL_RUN_LAST, None,
                   (GObject.TYPE_PYOBJECT,))
