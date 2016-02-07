#!/usr/bin/env python
# encoding: utf-8
""" Wrappers around standard library functions used in vimiv """

import os
import sys


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
        files = os.listdir(os.path.expanduser(path))
        for fil in files:
            if not fil.startswith("."):
                yield fil

    return files
