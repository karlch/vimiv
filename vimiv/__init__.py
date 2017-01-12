# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""vimiv init: tests some imports and imports main."""

import sys

try:
    from gi import require_version
    require_version('Gtk', '3.0')
    from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Pango
    from PIL import Image, ImageEnhance
    import vimiv

except ImportError as import_error:
    message = import_error.msg + "\n" + "Are all dependencies installed?"
    print(message)
    sys.exit(1)
