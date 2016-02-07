#!/usr/bin/env python
# encoding: utf-8
""" All actions for the vimiv image mode """

import os
from random import shuffle
from gi.repository import GdkPixbuf, GLib


def image_size(vimiv):
    """ Returns the size of the image depending on what other widgets
    are visible and if fullscreen or not """
    if vimiv.settings["GENERAL"]["fullscreen"]:
        size = vimiv.screensize
    else:
        size = vimiv.get_size()
    if vimiv.settings["LIBRARY"]["show_library"]:
        size = (size[0] - vimiv.settings["LIBRARY"]["library_width"], size[1])
    # if not self.sbar:
    #     size = (size[0], size[1] - self.statusbar_size - 24)
    return size


def get_zoom_percent(vimiv, imsize, zWidth=False, zHeight=False):
    """ Returns the current zoom factor """
    # Size of the file
    pboWidth = vimiv.pixbufOriginal.get_width()
    pboHeight = vimiv.pixbufOriginal.get_height()
    pboScale = pboWidth / pboHeight
    # Size of the image to be shown
    wScale = imsize[0] / imsize[1]
    stickout = zWidth | zHeight

    # Image is completely shown and user doesn't want overzoom
    if (pboWidth < imsize[0] and pboHeight < imsize[1] and
            not (stickout or vimiv.settings["GENERAL"]["overzoom"])):
        return 1
    # "Portrait" image
    elif (pboScale < wScale and not stickout) or zHeight:
        return imsize[1] / pboHeight
    # "Panorama/landscape" image
    else:
        return imsize[0] / pboWidth


def update_image(vimiv, zoom_percent, update_info=True, update_gif=True):
    """ Show the final image """
    if not vimiv.paths:
        return
    pboWidth = vimiv.pixbufOriginal.get_width()
    pboHeight = vimiv.pixbufOriginal.get_height()

    scrolled_win = vimiv.box.get_children()[0].get_children()[1]
    image = scrolled_win.get_child().get_child()

    # try:  # If possible scale the image
    pbfWidth = int(pboWidth * zoom_percent)
    pbfHeight = int(pboHeight * zoom_percent)
    # Rescaling of svg
    ending = vimiv.paths[vimiv.index].split("/")[-1].split(".")[-1]
    if ending == "svg" and vimiv.rescale_svg:
        pixbufFinal = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            vimiv.paths[vimiv.index], -1, pbfHeight, True)
    else:
        pixbufFinal = vimiv.pixbufOriginal.scale_simple(
            pbfWidth, pbfHeight, GdkPixbuf.InterpType.BILINEAR)
    image.set_from_pixbuf(pixbufFinal)
    # except:  # If not it must me an animation
    #     # TODO actual pause and play of Gifs
    #     vimiv.zoom_percent = 1
    #     if update_gif:
    #         if not vimiv.animation_toggled:
    #             vimiv.image.set_from_animation(vimiv.pixbufOriginal)
    #         else:
    #             pixbufFinal = vimiv.pixbufOriginal.get_static_image()
    #             vimiv.image.set_from_pixbuf(pixbufFinal)
    # Update the statusbar if required
    # if update_info:
    #     vimiv.update_info()


def move_index(vimiv, forward=True, key=False, delta=1, force=False):
    """ Move by delta in the path """
    # Check if an image is opened
    if not vimiv.paths or vimiv.thumbnail_toggled:
        return
    # Check if image has been edited
    # if vimiv.check_for_edit(force):
    #     return
    # Check for prepended numbers
    # if key and vimiv.num_str:
    #     delta *= int(vimiv.num_str)
    # Forward or backward
    if not forward:
        delta *= -1
    vimiv.index = (vimiv.index + delta) % len(vimiv.paths)
    vimiv.user_zoomed = False

    # Reshuffle on wrap-around
    shuffle_paths = vimiv.settings["GENERAL"]["shuffle"]
    if shuffle_paths and vimiv.index is 0 and delta > 0:
        shuffle(vimiv.paths)

    path = vimiv.paths[vimiv.index]
    try:
        if not os.path.exists(path):
            print("Error: Couldn't open", path)
            # vimiv.delete()
            return
        else:
            vimiv.pixbufOriginal = GdkPixbuf.PixbufAnimation.new_from_file(
                path)
        if vimiv.pixbufOriginal.is_static_image():
            vimiv.pixbufOriginal = vimiv.pixbufOriginal.get_static_image()
            imsize = image_size(vimiv)
            zoom_percent = get_zoom_percent(vimiv, imsize)
        else:
            zoom_percent = 1
        # If one simply reloads the file the info shouldn't be updated
        if delta:
            update_image(vimiv, zoom_percent)
        else:
            update_image(vimiv, zoom_percent, False)

    except GLib.Error:  # File not accessible
        vimiv.paths.remove(path)
        vimiv.err_message("Error: file not accessible")
        vimiv.move_pos(False)

    # vimiv.num_clear()
    return True  # for the slideshow


def auto_resize(vimiv, widget):
    """ Automatically resize image when window is resized """
    # if vimiv.get_size() != vimiv.winsize:
    #     vimiv.winsize = vimiv.get_size()
    #     if vimiv.paths and not vimiv.user_zoomed:
    vimiv.zoom_to(0)
        # elif not vimiv.paths and vimiv.expand_lib:
        #     vimiv.grid.set_size_request(vimiv.winsize[0], 10)
        # vimiv.cmd_line_info.set_max_width_chars(vimiv.winsize[0]/16)
