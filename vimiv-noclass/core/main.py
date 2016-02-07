#!/usr/bin/env python
# encoding: utf-8
""" Main function for the vimiv image browser
Calls the necessary functions and runs them """

from vimiv.core.parse_args import get_args, parse_args
from vimiv.core.parse_dirs import parse_dirs
from vimiv.core.parse_config import parse_config
from vimiv.core.run_vimiv import run


def main():
    """ Starting point for vimiv """
    parser = get_args()
    parse_dirs()
    settings = parse_config()
    settings = parse_args(parser, settings)
    run(settings)
