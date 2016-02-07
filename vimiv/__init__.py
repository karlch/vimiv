#!/usr/bin/env python3
# encoding: utf-8

try:
    import argparse
    import configparser
    import mimetypes
    import os
    import re
    import shutil
    import signal
    import sys
    from gi import require_version
    require_version('Gtk', '3.0')
    from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Pango
    from random import shuffle
    from subprocess import Popen, PIPE
    from threading import Thread
    from PIL import Image, ImageEnhance

except ImportError as import_error:
    print(import_error)
    print("Are all dependencies installed?")
    sys.exit(1)

from vimiv.main import main
