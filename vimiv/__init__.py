#!/usr/bin/env python3
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""vimiv init: tests some imports and imports main."""

import sys

try:
    from gi import require_version
    require_version('Gtk', '3.0')
    from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Pango
    from PIL import Image, ImageEnhance
    from vimiv.helpers import error_message

except ImportError as import_error:
    message = import_error.msg + "\n" + "Are all dependencies installed?"
    error_message(message)
    sys.exit(1)
