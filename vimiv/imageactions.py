# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Actions which act on the actual image file."""

import os
import hashlib
import tempfile
from shutil import which
from subprocess import PIPE, Popen
from multiprocessing import Pool

import collections

from gi._error import GError
from gi.repository import GdkPixbuf, Gtk, GLib
from PIL import Image


def save_image(im, filename):
    """Save the image with all the exif keys that exist.

    Args:
        im: PIL image to act on.
        filename: Name of the image to save.
    """
    kwargs = im.info
    im.save(filename, **kwargs)


def rotate_file(filelist, cwise):
    """Rotate every image in filelist cwise*90° counterclockwise.

    Args:
        filelist: List of files to operate on.
        cwise: Rotation amount. Rotation is cwise*90° counterclockwise.
    """
    # Always work on realpath, not on symlink
    filelist = [os.path.realpath(image) for image in filelist]
    for image in filelist:
        with Image.open(image) as im:
            if cwise == 1:
                im = im.transpose(Image.ROTATE_90)
            elif cwise == 2:
                im = im.transpose(Image.ROTATE_180)
            elif cwise == 3:
                im = im.transpose(Image.ROTATE_270)
            save_image(im, image)


def flip_file(filelist, horizontal):
    """Flip every image in the correct direction.

    Args:
        filelist: List of files to operate on.
        horizontal: If True, flip horizontally. Else flip vertically.
    """
    # Always work on realpath, not on symlink
    filelist = [os.path.realpath(image) for image in filelist]
    for image in filelist:
        with Image.open(image) as im:
            if horizontal:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            save_image(im, image)


def autorotate(filelist, method="auto"):
    """Autorotate all pictures in filelist according to exif information.

    Args:
        filelist: List of files to operate on.
        method: Method to use. Auto tries jhead and falls back to PIL.
    """
    rotated_images = 0
    # Check for which method in auto
    if method == "auto":
        method = "jhead" if which("jhead") else "PIL"
    # jhead does this better
    if method == "jhead":
        cmd = ["jhead", "-autorot", "-ft"] + filelist
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        out = out.decode(encoding="UTF-8")
        err = err.decode(encoding="UTF-8")
        # Find out how many images were rotated
        for line in out.split("\n"):
            if "Modified" in line and line.split()[1] not in err:
                rotated_images += 1
        # Added to the message displayed when done
        method = "jhead"
    elif method == "PIL":
        for path in filelist:
            with Image.open(path) as im:
                exif = im._getexif()
                orientation_key = 274  # cf ExifTags
                rotated = True

                # Only do something if orientation info is there
                if exif and orientation_key in exif:
                    orientation = exif[orientation_key]
                    # Rotate and save the image
                    if orientation == 3:
                        im = im.transpose(Image.ROTATE_180)
                    elif orientation == 6:
                        im = im.transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        im = im.transpose(Image.ROTATE_90)
                    else:
                        rotated = False
                    if rotated:
                        save_image(im, path)
                        rotated_images += 1
            method = "PIL"

    # Return the amount of rotated images and the method used
    return rotated_images, method


ThumbTuple = collections.namedtuple('ThumbTuple', ['original', 'thumbnail'])


class Thumbnails:
    """Thumbnail creation class.

    Attributes:
        filelist: List of files to operate on.
        large: the thumbnail managing standard specifies two thumbnail sizes
               256x256 (large) and 128x128 (normal)
        default_thumbnail: Default icon if thumbnail creation fails.
    """

    def __init__(self, filelist, large=True):
        """Create default settings.

        Args:
            filelist: List of files to operate on.
            large: Size of thumbnails that are created.
        """
        self.filelist = filelist
        self.large = large
        self.thumbnail_manager = ThumbnailManager()

        # Default icon if thumbnail creation fails
        icon_theme = Gtk.IconTheme.get_default()
        icon_info = icon_theme.lookup_icon("dialog-error", 256, 0)
        self.default_thumbnail = icon_info.get_filename()

    def _get_thumbnail_tuple(self, source_file):
        thumbnail_path = self.thumbnail_manager.get_thumbnail(source_file)
        if thumbnail_path is None:
            thumbnail_path = self.default_thumbnail
        return ThumbTuple(original=source_file, thumbnail=thumbnail_path)

    def thumbnails_create(self):
        """Create thumbnails for all images in filelist if they do not exist."""

        with Pool(os.cpu_count() + 1) as pool:
            thumb_list = pool.map(self._get_thumbnail_tuple, self.filelist)

        return thumb_list


class ThumbnailManager(object):
    """The ThumbnailManager implements freedestop.org's Thumbnail Managing
    Standard.
    """

    KEY_URI = "Thumb::URI"
    KEY_MTIME = "Thumb::MTime"
    KEY_SIZE = "Thumb::Size"
    KEY_WIDTH = "Thumb::Image::Width"
    KEY_HEIGHT = "Thumb::Image::Height"

    def __init__(self, large=True):
        super(ThumbnailManager, self).__init__()
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
