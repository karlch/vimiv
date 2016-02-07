#!/usr/bin/env python
# encoding: utf-8
""" The argparser for vimiv """
import argparse


def get_args():
    """ Create the argparse parser and return it """
    usage = '%(prog)s [options] [paths ...]'
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("-b", "--bar", action="store_true", dest="sbar",
                        help="display statusbar")
    parser.add_argument("-B", "--no-bar", action="store_false", dest="sbar",
                        help="hide statusbar")
    parser.add_argument("-l", "--library", action="store_true",
                        dest="library", help="display library")
    parser.add_argument("-L", "--no-library", action="store_false",
                        dest="library", help="don't display library")
    parser.add_argument("-f", "--fullscreen", action="store_true",
                        dest="fullscreen", help="start in fullscreen")
    parser.add_argument("-F", "--no-fullscreen", action="store_false",
                        dest="fullscreen", help="don't start in fullscreen")
    parser.add_argument("-s", "--shuffle", action="store_true",
                        dest="shuffle", help="shuffle filelist")
    parser.add_argument("-S", "--no-shuffle", action="store_false",
                        dest="shuffle", help="don't shuffle the filelist")
    parser.add_argument("-r", "--recursive", action="store_true",
                        dest="recursive",
                        help="search given directories recursively")
    parser.add_argument("-R", "--no-recursive", action="store_false",
                        dest="recursive",
                        help="don't search given directories recursively")
    parser.add_argument("--slideshow", action="store_true",
                        help="start slideshow immediately")
    parser.add_argument("--start-from-desktop", action="store_true",
                        help="start using the desktop_start_dir as path",
                        dest="desktop")
    parser.add_argument("--slideshow-delay", type=float,
                        help="set the slideshow delay")
    parser.add_argument("-g", "--geometry", dest="geometry",
                        help="set the starting geometry")
    parser.add_argument("path", nargs='*', default=[])

    return parser


def parse_args(parser, settings):
    """ Parse the arguments and return the modified settings """
    args = parser.parse_args()
    settings["GENERAL"]["display_bar"] = args.sbar
    settings["GENERAL"]["recursive"] = args.recursive
    settings["GENERAL"]["start_fullscreen"] = args.fullscreen
    settings["GENERAL"]["shuffle"] = args.shuffle
    settings["GENERAL"]["slideshow_delay"] = args.slideshow_delay
    settings["GENERAL"]["start_slideshow"] = args.slideshow
    settings["GENERAL"]["geometry"] = args.geometry
    settings["LIBRARY"]["show_library"] = args.library
    settings["GENERAL"]["start_from_desktop"] = args.desktop
    settings["GENERAL"]["paths"] = args.path

    return settings
