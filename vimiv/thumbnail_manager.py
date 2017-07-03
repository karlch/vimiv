# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Provides classes to store and load thumbnails from a shared cache.

The ThumbnailStore transparently creates and loads thumbnails according to the
freedesktop.org thumbnail management standard.
The ThumbnailManager provides a asynchronous mechanism to load thumbnails from
the store.

If possible, you should avoid using the store directly but use the manager
instead.
"""

import collections
import hashlib
import os
import tempfile
from multiprocessing.pool import ThreadPool as Pool

from PIL import Image
from gi._error import GError
from gi.repository import Gtk, GLib, GdkPixbuf
from gi.repository.GdkPixbuf import Pixbuf

ThumbTuple = collections.namedtuple('ThumbTuple', ['original', 'thumbnail'])


class ThumbnailManager:
    """Provides an asynchronous mechanism to load thumbnails.

    Attributes:
        thumbnail_store: ThumbnailStore class with the loading mechanism.
        large: The thumbnail managing standard specifies two thumbnail sizes.
            256x256 (large) and 128x128 (normal)
        default_icon: Default icon if thumbnails are not yet loaded.
        error_icon: The path to the icon which is used, when thumbnail creation
                    fails.
    """

    _cpu_count = os.cpu_count()
    if _cpu_count is None:
        _cpu_count = 1
    elif _cpu_count > 1:
        _cpu_count -= 1

    _thread_pool = Pool(_cpu_count)
    _cache = {}

    def __init__(self, large=True):
        """Construct a new ThumbnailManager.

        Args:
            large: Size of thumbnails that are created. If true 256x256 else
                   128x128.
        """
        super(ThumbnailManager, self).__init__()
        self.thumbnail_store = ThumbnailStore(large=large)

        # Default icon if thumbnail creation fails
        icon_theme = Gtk.IconTheme.get_default()
        self.error_icon = icon_theme.lookup_icon("dialog-error", 256,
                                                 0).get_filename()
        self.default_icon = icon_theme.lookup_icon("image-x-generic", 256,
                                                   0).get_filename()

    def _do_get_thumbnail_at_scale(self, source_file, size, callback, index,
                                   ignore_cache=False):
        if not ignore_cache and source_file in self._cache:
            pixbuf = self._cache[source_file]
        else:
            thumbnail_path = self.thumbnail_store.get_thumbnail(source_file,
                                                                ignore_cache)
            if thumbnail_path is None:
                thumbnail_path = self.error_icon
            pixbuf = Pixbuf.new_from_file(thumbnail_path)
            self._cache[source_file] = pixbuf

        if pixbuf.get_height() != size and pixbuf.get_width != size:
            pixbuf = self.scale_pixbuf(pixbuf, size)

        return callback, pixbuf, index

    @staticmethod
    def scale_pixbuf(pixbuf, size):
        """Scale the pixbuf to the given size keeping the aspect ratio.

        Either the width or the height of the returned pixbuf is `size` large,
        depending on the aspect ratio.

        Args:
            pixbuf: The pixbuf to scale
            size: The size of the new width or height

        Return:
            The scaled pixbuf.
        """
        width = size
        height = size
        ratio = pixbuf.get_width() / pixbuf.get_height()
        if ratio > 1:
            height /= ratio
        else:
            width *= ratio

        pixbuf = pixbuf.scale_simple(width, height,
                                     GdkPixbuf.InterpType.BILINEAR)
        return pixbuf

    @staticmethod
    def _do_callback(result):
        GLib.idle_add(*result)

    def get_thumbnail_at_scale_async(self, filename, size, callback, index,
                                     ignore_cache=False):
        """Create the thumbnail for 'filename' and return it via 'callback'.

        Creates the thumbnail for the given filename at the given size and
        then calls the given callback function with the resulting pixbuf.

        Args:
            filename: The filename to get the thumbnail for
            size: The size the returned pixbuf is scaled to
            callback: A callable of form callback(pixbuf, *args)
            args: Any additional arguments that can be passed to callback
            ignore_cache: If true, the builtin in-memory cache is bypassed and
                          the thumbnail file is loaded from disk
        """
        self._thread_pool.apply_async(self._do_get_thumbnail_at_scale,
                                      (filename, size, callback, index,
                                       ignore_cache),
                                      callback=self._do_callback)


class ThumbnailStore(object):
    """Implements freedesktop.org's Thumbnail Managing Standard."""

    KEY_URI = "Thumb::URI"
    KEY_MTIME = "Thumb::MTime"
    KEY_SIZE = "Thumb::Size"
    KEY_WIDTH = "Thumb::Image::Width"
    KEY_HEIGHT = "Thumb::Image::Height"

    def __init__(self, large=True):
        """Construct a new ThumbnailStore.

        Args:
            large: Size of thumbnails that are created. If true 256x256 else
                   128x128.
        """
        super(ThumbnailStore, self).__init__()
        import vimiv
        self.base_dir = os.path.join(GLib.get_user_cache_dir(), "thumbnails")
        self.fail_dir = os.path.join(
            self.base_dir, "fail", "vimiv-" + vimiv.__version__)
        self.thumbnail_dir = ""
        self.thumb_size = 0
        self.use_large_thumbnails(large)
        self._ensure_dirs_exist()

    def use_large_thumbnails(self, enabled=True):
        """Specify whether this thumbnail store uses large thumbnails.

        Large thumbnails have 256x256 pixels and non-large thumbnails 128x128.

        Args:
            enabled: If true large thumbnails will be used.
        """
        if enabled:
            self.thumbnail_dir = os.path.join(self.base_dir, "large")
            self.thumb_size = 256
        else:
            self.thumbnail_dir = os.path.join(self.base_dir, "normal")
            self.thumb_size = 128

    def get_thumbnail(self, filename, ignore_current=False):
        """Get the path of the thumbnail of the given filename.

        If the requested thumbnail does not yet exist, it will first be created
        before returning its path.

        Args:
            filename: The filename to get the thumbnail for.
            ignore_current: If True, ignore saved thumbnails and force a
                recreation. Needed as transforming images from within thumbnail
                mode may happen faster than in 1s.

        Returns:
            The path of the thumbnail file or None if thumbnail creation failed.
        """
        # Don't create thumbnails for thumbnail cache
        if filename.startswith(self.base_dir):
            return filename

        thumbnail_filename = self._get_thumbnail_filename(filename)
        thumbnail_path = self._get_thumbnail_path(thumbnail_filename)
        if os.access(thumbnail_path, os.R_OK) \
                and self._is_current(filename, thumbnail_path) \
                and not ignore_current:
            return thumbnail_path

        fail_path = self._get_fail_path(thumbnail_filename)
        if os.path.exists(fail_path):
            # We already tried to create a thumbnail for the given file but
            # failed; don't try again.
            return None

        if self._create_thumbnail(filename, thumbnail_filename):
            return thumbnail_path

        return None

    def _ensure_dirs_exist(self):
        os.makedirs(self.thumbnail_dir, 0o700, exist_ok=True)
        os.makedirs(self.fail_dir, 0o700, exist_ok=True)

    def _is_current(self, source_file, thumbnail_path):
        source_mtime = str(self._get_source_mtime(source_file))
        thumbnail_mtime = self._get_thumbnail_mtime(thumbnail_path)
        return source_mtime == thumbnail_mtime

    def _get_thumbnail_filename(self, filename):
        uri = self._get_source_uri(filename)
        return hashlib.md5(bytes(uri, "UTF-8")).hexdigest() + ".png"

    @staticmethod
    def _get_source_uri(filename):
        return "file://" + os.path.abspath(os.path.expanduser(filename))

    def _get_thumbnail_path(self, thumbnail_filename):
        return os.path.join(self.thumbnail_dir, thumbnail_filename)

    def _get_fail_path(self, thumbnail_filename):
        return os.path.join(self.fail_dir, thumbnail_filename)

    @staticmethod
    def _get_source_mtime(src):
        return int(os.path.getmtime(src))

    def _get_thumbnail_mtime(self, thumbnail_path):
        with Image.open(thumbnail_path) as image:
            mtime = image.info[self.KEY_MTIME]

        return mtime

    def _create_thumbnail(self, source_file, thumbnail_filename):
        # Cannot access source; create neither thumbnail nor fail file
        if not os.access(source_file, os.R_OK):
            return False

        try:
            image = Pixbuf.new_from_file_at_scale(source_file, self.thumb_size,
                                                  self.thumb_size, True)
            dest_path = self._get_thumbnail_path(thumbnail_filename)
            success = True
        except GError:
            image = Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 1, 1)
            dest_path = self._get_fail_path(thumbnail_filename)
            success = False

        width = 0
        height = 0
        try:
            with Image.open(source_file) as img:
                width = img.size[0]
                height = img.size[1]
        except IOError:
            pass

        options = {
            "tEXt::" + self.KEY_URI: str(self._get_source_uri(source_file)),
            "tEXt::" + self.KEY_MTIME: str(self._get_source_mtime(source_file)),
            "tEXt::" + self.KEY_SIZE: str(os.path.getsize(source_file))
        }

        if width > 0 and height > 0:
            options["tEXt::" + self.KEY_WIDTH] = str(width)
            options["tEXt::" + self.KEY_HEIGHT] = str(height)

        # First create temporary file and then move it. This avoids problems
        # with concurrent access of the thumbnail cache, since "move" is an
        # atomic operation
        handle, tmp_filename = tempfile.mkstemp(dir=self.base_dir)
        os.close(handle)
        os.chmod(tmp_filename, 0o600)
        image.savev(tmp_filename, "png", list(options.keys()),
                    list(options.values()))
        os.replace(tmp_filename, dest_path)

        return success
