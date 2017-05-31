# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Wrapper functions for the _image_enhance C extension."""

from gi.repository import Gdk

from vimiv import _image_enhance


def enhance_bc(pixbuf, brightness, contrast):
    """Enhance brightness and contrast of a GdkPixbuf.Pixbuf.

    Args:
        pixbuf: Original GdkPixbuf.Pixbuf to work with.
        brightness: Integer value between -127 and 127 to change brightness.
        contrast: Integer value between -127 and 127 to change contrast.
    Return:
        The enhanced GdkPixbuf.Pixbuf
    """
    # Work with Cairo surface as this can be transformed from and to bytes
    # quickly
    surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 1, None)
    width = surface.get_width()
    height = surface.get_height()
    data = surface.get_data().tobytes()
    # Update plain bytes using C extension
    # Pylint does not read this properly
    # pylint: disable=no-member
    data = _image_enhance.enhance_bc(data, brightness, contrast)
    surface = surface.create_for_data(data, surface.get_format(), width,
                                      height, surface.get_stride())
    # Create pixbuf from updated surface
    return Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
