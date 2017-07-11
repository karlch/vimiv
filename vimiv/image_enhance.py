# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Wrapper functions for the _image_enhance C extension."""

from gi.repository import GdkPixbuf, GLib

from vimiv import _image_enhance


def enhance_bc(pixbuf, brightness, contrast):
    """Enhance brightness and contrast of a GdkPixbuf.Pixbuf.

    Args:
        pixbuf: Original GdkPixbuf.Pixbuf to work with.
        brightness: Float between 0.0 and 2.0 to change brightness.
        contrast: Float between 0.0 and 2.0 to change contrast.
    Return:
        The enhanced GdkPixbuf.Pixbuf
    """
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    data = pixbuf.get_pixels()
    has_alpha = pixbuf.get_has_alpha()
    rowstride = 4 * width if has_alpha else 3 * width
    # Update plain bytes using C extension
    # Pylint does not read this properly
    # pylint: disable=no-member
    data = _image_enhance.enhance_bc(data, brightness, contrast)
    gdata = GLib.Bytes.new(data)
    return GdkPixbuf.Pixbuf.new_from_bytes(
        gdata, GdkPixbuf.Colorspace.RGB, has_alpha, 8, width, height, rowstride)
