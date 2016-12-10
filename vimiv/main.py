#!/usr/bin/env python3
# encoding: utf-8
"""Main function for the vimiv["image"] browser.

Parses the necessary stuff and starts the Gtk instance.
"""

import signal
from vimiv.configparser import parse_dirs, parse_config
from vimiv.app import Vimiv


def main(arguments, vimiv_id="org.vimiv"):
    """Starting point for vimiv.

    Args:
        arguments: Arguments passed to the commandline.
        vimiv_id: The ID used to register vimiv.
    Return:
        The generated main vimiv application.
    """
    parse_dirs()
    settings = parse_config()

    # Start the actual window
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # ^C
    vimiv = Vimiv(vimiv_id)
    vimiv.set_settings(settings)
    return vimiv
