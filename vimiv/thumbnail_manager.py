import collections
import hashlib
import os
import tempfile
from multiprocessing.pool import ThreadPool as Pool

from PIL import Image
from gi._error import GError
from gi.repository import Gtk, GLib, GdkPixbuf

ThumbTuple = collections.namedtuple('ThumbTuple', ['original', 'thumbnail'])


class ThumbnailManager:
    """Thumbnail creation class.

    Attributes:
        filelist: List of files to operate on.
        large: the thumbnail managing standard specifies two thumbnail sizes
               256x256 (large) and 128x128 (normal)
        default_thumbnail: Default icon if thumbnail creation fails.
    """

    _cpu_count = os.cpu_count()
    if _cpu_count is None:
        _cpu_count = 1
    elif _cpu_count > 1:
        _cpu_count -= 1

    _thread_pool = Pool(_cpu_count)

    def __init__(self, large=True):
        """Create default settings.

        Args:
            filelist: List of files to operate on.
            large: Size of thumbnails that are created.
        """
        super(ThumbnailManager, self).__init__()
        self.thumbnail_store = ThumbnailStore(large=large)

        # Default icon if thumbnail creation fails
        icon_theme = Gtk.IconTheme.get_default()
        self.error_icon = icon_theme.lookup_icon("dialog-error", 256, 0).get_filename()
        self.default_icon = icon_theme.lookup_icon("image-x-generic", 256, 0).get_filename()

    def _get_thumbnail_tuple(self, source_file, position, callback):
        thumbnail_path = self.thumbnail_store.get_thumbnail(source_file)
        if thumbnail_path is None:
            thumbnail_path = self.error_icon
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumbnail_path)

        return callback, position, pixbuf

    @staticmethod
    def _do_callback(result):
        GLib.idle_add(*result)

    def get_thumbnail_pixbuf_async(self, filename, position, callback):
        self._thread_pool.apply_async(self._get_thumbnail_tuple, (filename, position, callback),
                                      callback=self._do_callback)


class ThumbnailStore(object):
    """The ThumbnailManager implements freedestop.org's Thumbnail Managing
    Standard.
    """

    KEY_URI = "Thumb::URI"
    KEY_MTIME = "Thumb::MTime"
    KEY_SIZE = "Thumb::Size"
    KEY_WIDTH = "Thumb::Image::Width"
    KEY_HEIGHT = "Thumb::Image::Height"

    def __init__(self, large=True):
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
        if enabled:
            self.thumbnail_dir = os.path.join(self.base_dir, "large")
            self.thumb_size = 256
        else:
            self.thumbnail_dir = os.path.join(self.base_dir, "normal")
            self.thumb_size = 128

    def get_thumbnail(self, filename):

        # Don't create thumbnails for thumbnail cache
        if filename.startswith(self.base_dir):
            return filename

        thumbnail_filename = self._get_thumbnail_filename(filename)
        thumbnail_path = self._get_thumbnail_path(thumbnail_filename)
        if os.access(thumbnail_path, os.R_OK) \
                and self._is_current(filename, thumbnail_path):
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
        def ensure_dir_exists(directory):
            try:
                os.mkdir(directory)
                os.chmod(directory, 0o700)
            except FileExistsError:
                pass

        ensure_dir_exists(self.base_dir)
        ensure_dir_exists(self.thumbnail_dir)
        ensure_dir_exists(self.fail_dir)

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
            image = GdkPixbuf.Pixbuf.new_from_file_at_scale(source_file, self.thumb_size, self.thumb_size, True)
            dest_path = self._get_thumbnail_path(thumbnail_filename)
            success = True
        except GError:
            image = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 1, 1)
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
        image.savev(tmp_filename, "png", list(options.keys()), list(options.values()))
        os.replace(tmp_filename, dest_path)

        return success
