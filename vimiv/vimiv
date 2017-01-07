#!/usr/bin/env python3
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Vimiv executable."""
import signal
import sys
from vimiv.app import Vimiv

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    Vimiv().run(sys.argv)
