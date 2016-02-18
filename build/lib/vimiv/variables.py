#!/usr/bin/env python
# encoding: utf-8
""" Contains a few standard variables of vimiv """

from subprocess import Popen, PIPE
from gi.repository import GdkPixbuf, Gtk


# Supported mimetypes
types = []
for pixbuf_format in GdkPixbuf.Pixbuf.get_formats():
    types.extend(pixbuf_format.get_mime_types())
types.append("image/x-ms-bmp")

# Dictionary with all the scrolling
scrolltypes = {}
scrolltypes["h"] = (Gtk.ScrollType.STEP_BACKWARD, True)
scrolltypes["j"] = (Gtk.ScrollType.STEP_FORWARD, False)
scrolltypes["k"] = (Gtk.ScrollType.STEP_BACKWARD, False)
scrolltypes["l"] = (Gtk.ScrollType.STEP_FORWARD, True)
scrolltypes["H"] = (Gtk.ScrollType.START, True)
scrolltypes["J"] = (Gtk.ScrollType.END, False)
scrolltypes["K"] = (Gtk.ScrollType.START, False)
scrolltypes["L"] = (Gtk.ScrollType.END, True)

# A list of all external commands
external_commands = []
try:
    p = Popen('echo $PATH | tr \':\' \'\n\' | xargs -n 1 ls -1',
              stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    out = out.decode('utf-8').split()
    for cmd in sorted(list(set(out))):
        external_commands.append("!" + cmd)
except:
    external_commands = []
external_commands = tuple(external_commands)
