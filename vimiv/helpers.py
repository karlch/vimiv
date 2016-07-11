#!/usr/bin/env python3
# encoding: utf-8
""" Wrappers around standard library functions used in vimiv """

import os
import sys
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk

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


def import_wrapper(module):
    """ Wrapper function around the import statement with exception checking """
    try:
        import module
    except ImportError:
        print("Python module", module, "not found. Are all dependencies",
              "installed?")
        sys.exit(1)


def listdir_wrapper(path, show_hidden=False):
    """ Reimplementation of os.listdir which mustn't show hidden files """
    if show_hidden:
        files = os.listdir(os.path.expanduser(path))
    else:
        files = listdir_nohidden(path)

    return sorted(list(files))


def listdir_nohidden(path):
    """ The nohidden part of listdir_wrapper """
    files = os.listdir(os.path.expanduser(path))
    for fil in files:
        if not fil.startswith("."):
            yield fil


def read_file(filename):
    """ Reads the contents of a file into a list and returns it. If the file
    doesn't exist it will be created and an empty list returned. """
    content = []
    try:
        fil = open(filename, "r")
        for line in fil:
            content.append(line.rstrip("\n"))
    except:
        fil = open(filename, "w")
        fil.write("")
    fil.close()
    return content
