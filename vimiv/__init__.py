#!/usr/bin/env python3
# encoding: utf-8
""" vimiv init: tests some imports and imports main """

import sys

try:
    from gi import require_version
    require_version('Gtk', '3.0')
    from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Pango
    from PIL import Image, ImageEnhance

except ImportError as import_error:
    print(import_error)
    print("Are all dependencies installed?")
    sys.exit(1)

import vimiv.main
