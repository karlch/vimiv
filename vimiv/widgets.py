#!/usr/bin/env python3
# encoding: utf-8
""" Generates most of the widgets needed for Vimiv """

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango
from vimiv.actions import keys  # TODO
# from vimiv.actions import commands # TODO


def cmd_line_generate(vimiv):
    """ Creates the command line """
    cmd_line_box = Gtk.HBox(False, 0)
    cmd_line = Gtk.Entry()
    # cmd_line.connect("activate", commandline.cmd_handler)
    cmd_line.connect("key_press_event", keys.handle_key_press, "COMMAND", vimiv)
    # cmd_line.connect("changed", cmd_check_close)
    cmd_line_info = Gtk.Label()
    # cmd_line_info.set_max_width_chars(winsize[0]/16)
    cmd_line_info.set_ellipsize(Pango.EllipsizeMode.END)
    cmd_line_box.pack_start(cmd_line, True, True, 0)
    cmd_line_box.pack_end(cmd_line_info, False, False, 0)

    return cmd_line_box


def statusbar_generate():
    """ Creates the statusbar """
    labelbox = Gtk.HBox(False, 0)
    # Position and image name
    left_label = Gtk.Label()  # Position and image name
    left_label.set_justify(Gtk.Justification.LEFT)
    # Mode and prefixed numbers
    right_label = Gtk.Label()  # Mode and prefixed numbers
    right_label.set_justify(Gtk.Justification.RIGHT)
    # Zoom, marked, slideshow...
    center_label = Gtk.Label()  # Zoom, marked, slideshow, ...
    center_label.set_justify(Gtk.Justification.CENTER)

    labelbox.pack_start(left_label, False, False, 0)
    labelbox.pack_start(center_label, True, True, 0)
    labelbox.pack_end(right_label, False, False, 0)

    return labelbox


def main_box_generate(vimiv):
    """ Creates the box in which everything gets packed
    structure:                      box
              hbox                  statusbox                     manipulate_box
    library_box   scrolled_win    label_box cmd_line_box
                     image         le ce ri  line  info
    """
    box = Gtk.VBox()
    # Horizontal box with image and treeview
    hbox = Gtk.HBox(False, 0)
    box.pack_start(hbox, True, True, 0)

    # Scrollable window for the image
    scrolled_win = Gtk.ScrolledWindow()
    hbox.pack_end(scrolled_win, True, True, 0)
    viewport = Gtk.Viewport()
    image = Gtk.Image()
    scrolled_win.add(viewport)
    viewport.add(image)
    scrolled_win.connect("key_press_event", keys.handle_key_press, "IMAGE",
                         vimiv)
    scrolled_win.grab_focus()

    # Command line and statusbar
    cmd_line_box = cmd_line_generate(vimiv)
    label_box = statusbar_generate()
    status_box = Gtk.VBox(False, 0)
    status_box.pack_start(label_box, False, False, 0)
    status_box.pack_end(cmd_line_box, False, False, 0)
    status_box.set_border_width(12)
    box.pack_end(status_box, False, False, 0)

    # Library
    # library_generate() TODO
    library_box = Gtk.HBox()
    hbox.pack_start(library_box, False, False, 0)

    # Manipulate bar
    # manipulate() TODO
    manipulate_box = Gtk.HBox()
    box.pack_end(manipulate_box, False, False, 0)

    vimiv.add(box)
    return box
