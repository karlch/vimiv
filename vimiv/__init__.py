#!/usr/bin/env python3
# encoding: utf-8
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
    print(message)
    error_message(message)
    sys.exit(1)

import vimiv.main
