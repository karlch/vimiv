#!/usr/bin/python3
# encoding: utf-8

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
from vimiv.variables import types, scrolltypes, external_commands
from vimiv.fileactions import populate

# Directories
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
trashdir = os.path.join(vimivdir, "Trash")
thumbdir = os.path.join(vimivdir, "Thumbnails")
tagdir = os.path.join(vimivdir, "Tags")


class Vimiv(Gtk.Window):
    """ Actual vimiv class as a Gtk Window """

    def __init__(self, settings, paths, index):

        self.paths = paths
        self.index = index

        # Default values
        self.animation_toggled = False
        self.thumbnail_toggled = False
        self.marked = []
        self.marked_bak = []  # saves marked images after marked toggle
        self.manipulate_toggled = False
        self.user_zoomed = False  # checks if the user manually zoomed the
        #                          image, necessary for the auto_resize function
        self.library_focused = False
        self.num_str = ""  # used to prepend actions with numbers
        self.dir_pos = {}  # Remembers positions in the library browser
        self.error = []
        # Dictionary for all the possible editing
        self.manipulations = [1, 1, 1, False]
        # Dictionary with command names and the corresponding functions
        self.commands = {"accept_changes": [self.button_clicked, "w", True],
                         "autorotate": [self.rotate_auto],
                         "center": [self.center_window],
                         "clear_trash": [self.clear, 'Trash'],
                         "clear_thumbs": [self.clear, 'Thumbnails'],
                         "command": [self.cmd_line_focus],
                         "delete": [self.delete],
                         "discard_changes": [self.button_clicked, "w", False],
                         "first":  [self.move_pos, False],
                         "first_lib":  [self.move_pos_lib, False],
                         "fit": [self.zoom_to, 0],
                         "fit_horiz": [self.zoom_to, 0, True, False],
                         "fit_vert": [self.zoom_to, 0, False, True],
                         "flip": [self.flip],
                         "format": [self.format_files],
                         "grow_lib": [self.resize_lib, None, True],
                         "last":  [self.move_pos, True],
                         "last_lib":  [self.move_pos_lib, True],
                         "library": [self.library_toggle],
                         "library_focus": [self.library_focus, True],
                         "library_unfocus": [self.library_focus, False],
                         "manipulate": [self.manipulate_toggle],
                         "mark": [self.mark],
                         "mark_all": [self.mark_all],
                         "mark_between": [self.mark_between],
                         "mark_toggle": [self.mark_toggle],
                         "move_up": [self.move_up],
                         "next": [self.move_index, True, True],
                         "next!": [self.move_index, True, True, 1, True],
                         "optimize": [self.cmd_edit, 'opt'],
                         "prev": [self.move_index, False, True],
                         "prev!": [self.move_index, False, True, 1, True],
                         "q": [self.quit],
                         "q!": [self.quit, True],
                         "reload_lib": [self.reload, '.'],
                         "rotate": [self.rotate],
                         "set animation!": [self.animation_toggle],
                         "set brightness": [self.cmd_edit, 'bri'],
                         "set contrast": [self.cmd_edit, 'con'],
                         "set library_width": [self.resize_lib],
                         "set overzoom!": [self.toggle_overzoom],
                         "set rescale_svg!": [self.toggle_rescale_svg],
                         "set sharpness": [self.cmd_edit, 'sha'],
                         "set show_hidden!": [self.hidden_toggle],
                         "set slideshow_delay": [self.set_slideshow_delay],
                         "set statusbar!": [self.toggle_statusbar],
                         "shrink_lib": [self.resize_lib, None, False],
                         "slideshow": [self.toggle_slideshow],
                         "slideshow_inc": [self.set_slideshow_delay, 2, "+"],
                         "slideshow_dec": [self.set_slideshow_delay, 2, "-"],
                         "tag_load": [self.tag_load],
                         "tag_remove": [self.tag_remove],
                         "tag_write": [self.tag_write],
                         "thumbnail": [self.thumbnail_toggle],
                         "zoom_in": [self.zoom_delta, +.25],
                         "zoom_out": [self.zoom_delta, -.25],
                         "zoom_to": [self.zoom_to]}

        self.functions = {"bri_focus": [self.focus_slider, "bri"],
                          "con_focus": [self.focus_slider, "con"],
                          "sha_focus": [self.focus_slider, "sha"],
                          "slider_dec": [self.change_slider, True, False],
                          "slider_inc": [self.change_slider, False, False],
                          "slider_dec_large": [self.change_slider, True, True],
                          "slider_inc_large": [self.change_slider, False, True],
                          "cmd_history_up": [self.history, False],
                          "cmd_history_down": [self.history, True],
                          "discard_command": [self.cmd_line_leave],
                          "complete": [self.cmd_complete],
                          "down": [self.scroll, "j"],
                          "down_lib": [self.scroll_lib, "j"],
                          "down_page": [self.scroll, "J"],
                          "left": [self.scroll, "h"],
                          "left_lib": [self.scroll_lib, "h"],
                          "left_page": [self.scroll, "H"],
                          "right": [self.scroll, "l"],
                          "right_lib": [self.scroll_lib, "l"],
                          "right_page": [self.scroll, "L"],
                          "up": [self.scroll, "k"],
                          "up_lib": [self.scroll_lib, "k"],
                          "up_page": [self.scroll, "K"],
                          "search": [self.cmd_search],
                          "fullscreen": [self.toggle_fullscreen]}
        self.functions.update(self.commands)

        # The configruations from vimivrc
        config = settings
        general = config["GENERAL"]
        library = config["LIBRARY"]
        # General
        self.fullscreen_toggled = general["start_fullscreen"]
        self.slideshow = general["start_slideshow"]
        self.slideshow_delay = general["slideshow_delay"]
        self.shuffle = general["shuffle"]
        self.sbar = general["display_bar"]
        self.winsize = general["geometry"]
        self.recursive = general["recursive"]
        self.rescale_svg = general["rescale_svg"]
        self.overzoom = general["overzoom"]
        self.thumbsize = general["thumbsize"]
        # Library
        self.library_toggled = library["show_library"]
        self.library_default_width = library["library_width"]
        self.library_width = self.library_default_width
        self.expand_lib = library["expand_lib"]
        self.border_width = library["border_width"]
        self.border_color = library["border_color"]
        self.show_hidden = library["show_hidden"]
        self.desktop_start_dir = library["desktop_start_dir"]

        # Keybindings
        self.keys = configparser.ConfigParser()
        if os.path.isfile(os.path.expanduser("~/.vimiv/keys.conf")):
            self.keys.read(os.path.expanduser("~/.vimiv/keys.conf"))
        elif os.path.isfile("/etc/vimiv/keys.conf"):
            self.keys.read("/etc/vimiv/keys.conf")
        else:
            print("Keyfile not found. Exiting.")
            sys.exit(1)

        # Cmd history from file
        self.cmd_history = []  # Remember cmd history
        histfile = os.path.expanduser("~/.vimiv/history")
        try:
            histfile = open(histfile, 'r')
            for line in histfile:
                self.cmd_history.append(line.rstrip("\n"))
        except:
            histfile = open(histfile, 'w')
            histfile.write("")
        histfile.close()
        self.cmd_pos = 0

        Gtk.Window.__init__(self)

    def delete(self):
        """ Delete all marked images or the current one """
        # Create the directory if it isn't there yet
        deldir = os.path.expanduser("~/.vimiv/Trash")
        if not os.path.isdir(deldir):
            os.mkdir(deldir)
        # Get all images
        images = self.manipulated_images("Deleted")
        for i, im in enumerate(images):
            if os.path.isdir(im):
                self.err_message("Deleting directories is not supported")
                return
            if os.path.exists(im):
                # Check if there is already a file with that name in the trash
                delfile = os.path.join(deldir, os.path.basename(im))
                if os.path.exists(delfile):
                    backnum = 1
                    ndelfile = delfile+"."+str(backnum)
                    while os.path.exists(ndelfile):
                        backnum += 1
                        ndelfile = delfile+"."+str(backnum)
                    shutil.move(delfile, ndelfile)
                shutil.move(im, deldir)
        self.reload_changes(os.path.abspath("."))
        self.marked = []

    def quit(self, force=False):
        for image in self.marked:
            print(image)
        # Check if image has been edited
        if self.check_for_edit(force):
            return
        # Save the history
        histfile = os.path.expanduser("~/.vimiv/history")
        histfile = open(histfile, 'w')
        for cmd in self.cmd_history:
            cmd += "\n"
            histfile.write(cmd)
        histfile.close()

        Gtk.main_quit()

    def check_for_edit(self, force):
        """ Checks if an image was edited before moving """
        if self.paths:
            if "EDIT" in self.paths[self.index]:
                if force:
                    self.button_clicked(False)
                    return 0
                else:
                    self.err_message("Image has been edited, add ! to force")
                    return 1

    def scroll(self, direction):
        """ Scroll the correct object """
        if self.thumbnail_toggled:
            self.thumbnail_move(direction)
        else:
            self.scrolled_win.emit('scroll-child',
                                   scrolltypes[direction][0],
                                   scrolltypes[direction][1])
        return True  # Deactivates default bindings (here for Arrows)

    def scroll_lib(self, direction):
        """ Scroll the library viewer and select if necessary """
        # Handle the specific keys
        if direction == "h":  # Behave like ranger
            self.remember_pos(os.path.abspath("."), self.treepos)
            self.move_up()
        elif direction == "l":
            self.file_select("a", Gtk.TreePath(self.treepos), "b", False)
        else:
            # Scroll the tree checking for a user step
            if self.num_str:
                step = int(self.num_str)
            else:
                step = 1
            if direction == "j":
                self.treepos = (self.treepos + step) % len(self.filelist)
            else:
                self.treepos = (self.treepos - step) % len(self.filelist)

            self.treeview.set_cursor(Gtk.TreePath(self.treepos), None, False)
            # Clear the user prefixed step
            self.num_clear()
        return True  # Deactivates default bindings (here for Arrows)

    def thumbnail_move(self, direction):
        """ Select thumbnails correctly and scroll """
        # Check for a user prefixed step
        if self.num_str:
            step = int(self.num_str)
        else:
            step = 1
        # Check for the specified thumbnail and handle exceptons
        if direction == "h":
            self.thumbpos -= step
        elif direction == "k":
            self.thumbpos -= self.columns*step
        elif direction == "l":
            self.thumbpos += step
        else:
            self.thumbpos += self.columns*step
        # Do not scroll to self.paths that don't exist
        if self.thumbpos < 0:
            self.thumbpos = 0
        elif self.thumbpos > (len(self.files)-len(self.errorpos)-1):
            self.thumbpos = len(self.files)-len(self.errorpos)-1
        # Move
        path = Gtk.TreePath.new_from_string(str(self.thumbpos))
        self.iconview.select_path(path)
        curthing = self.iconview.get_cells()[0]
        self.iconview.set_cursor(path, curthing, False)
        # Actual scrolling TODO
        self.thumbnail_scroll(direction, step, self.thumbpos)
        # Clear the user prefixed step
        self.num_clear()

    def thumbnail_scroll(self, direction, step, target):
        """ Handles the actual scrolling """
        # TODO
        if step == 0:
            step += 1
        # Vertical
        if direction == "k" or direction == "j":
            Gtk.Adjustment.set_step_increment(
                self.viewport.get_vadjustment(), (self.thumbsize[1]+30)*step)
            self.scrolled_win.emit('scroll-child',
                                   scrolltypes[direction][0], False)
        # Horizontal (tricky because one might reach a new column)
        else:
            start = target - step
            startcol = int(start / self.columns)
            endcol = int(target / self.columns)
            toscroll = endcol - startcol
            Gtk.Adjustment.set_step_increment(self.viewport.get_vadjustment(),
                                              (self.thumbsize[1]+30)*toscroll)
            self.scrolled_win.emit('scroll-child',
                                   scrolltypes[direction][0], False)

    def toggle_slideshow(self):
        """ Toggles the slideshow or updates the delay """
        if not self.paths:
            self.err_message("No valid self.paths, starting slideshow failed")
            return
        if self.thumbnail_toggled:
            self.err_message("Slideshow makes no sense in thumbnail mode")
            return
        # Delay changed via num_str?
        if self.num_str:
            self.set_slideshow_delay(float(self.num_str))
        # If the delay wasn't changed in any way just toggle the slideshow
        else:
            self.slideshow = not self.slideshow
            if self.slideshow:
                self.timer_id_s = GLib.timeout_add(1000*self.slideshow_delay,
                                                   self.move_index, True,
                                                   False, 1)
            else:
                GLib.source_remove(self.timer_id_s)
        self.update_info()

    def set_slideshow_delay(self, val, key=""):
        """ Sets slideshow delay to val or inc/dec depending on key """
        if key == "-":
            if self.slideshow_delay >= 0.8:
                self.slideshow_delay -= 0.2
        elif key == "+":
            self.slideshow_delay += 0.2
        elif val:
            self.slideshow_delay = float(val)
            self.num_str = ""
        # If slideshow was running reload it
        if self.slideshow:
            GLib.source_remove(self.timer_id_s)
            self.timer_id_s = GLib.timeout_add(1000*self.slideshow_delay,
                                               self.move_index, True, False, 1)
            self.update_info()

    def err_message(self, mes):
        """ Pushes an error message to the statusbar """
        self.error.append(1)
        mes = "<b>" + mes + "</b>"
        self.timer_id = GLib.timeout_add_seconds(5, self.error_false)
        if not self.sbar:
            self.left_label.set_markup(mes)
        else:  # Show bar if it isn't there
            self.toggle_statusbar()
            self.left_label.set_markup(mes)
            self.timer_id = GLib.timeout_add_seconds(5, self.toggle_statusbar)

    def error_false(self):
        self.error = self.error[0:-1]
        if not self.error:
            self.update_info()

    def toggle_fullscreen(self):
        self.fullscreen_toggled = not self.fullscreen_toggled
        if self.fullscreen_toggled:
            self.fullscreen()
        else:
            self.unfullscreen()
        # Adjust the image if necessary
        if self.paths:
            if self.user_zoomed:
                self.update_image()
            else:
                self.zoom_to(0)

    def toggle_statusbar(self):
        if not self.sbar and not self.cmd_line.is_visible():
            self.leftbox.hide()
        else:
            self.leftbox.show()
        self.sbar = not self.sbar
        # Resize the image if necessary
        if not self.user_zoomed and self.paths and not self.thumbnail_toggled:
            self.zoom_to(0)

    def toggle_rescale_svg(self):
        self.rescale_svg = not self.rescale_svg

    def toggle_overzoom(self):
        self.overzoom = not self.overzoom

    def save_image(self, im, filename):
        """ Saves the PIL image name with all the keys that exist """
        argstr = "filename"
        for key in im.info.keys():
            argstr += ", " + key + "=" + str(im.info[key])
        func = "im.save(" + argstr + ")"
        exec(func)

    def manipulated_images(self, message):
        """ Returns the images which should be manipulated - either the
            currently focused one or all marked images """
        images = []
        # Add the image shown
        if not self.marked and not self.thumbnail_toggled:
            if self.library_focused:
                images.append(os.path.abspath(self.files[self.treepos]))
            else:
                images.append(self.paths[self.index])
        # Add all marked images
        else:
            images = self.marked
            if len(images) == 1:
                err = "%s %d marked image" % (message, len(images))
            else:
                err = "%s %d marked images" % (message, len(images))
            self.err_message(err)
        # Delete all thumbnails of manipulated images
        thumbdir = os.path.expanduser("~/.vimiv/Thumbnails")
        thumbnails = os.listdir(thumbdir)
        for im in images:
            thumb = ".".join(im.split(".")[:-1]) + ".thumbnail" + ".png"
            thumb = thumb.split("/")[-1]
            if thumb in thumbnails:
                thumb = os.path.join(thumbdir, thumb)
                shutil.os.remove(thumb)

        return images

    def rotate(self, cwise):
        try:
            cwise = int(cwise)
            images = self.manipulated_images("Rotated")
            cwise = cwise % 4
            # Rotate the image shown
            if self.paths[self.index] in images:
                self.pixbufOriginal = self.pixbufOriginal.rotate_simple(
                    (90 * cwise))
                self.update_image(False)
            # Rotate all files in external thread
            rotate_thread = Thread(target=self.thread_for_rotate, args=(images,
                                                                        cwise))
            rotate_thread.start()
        except:
            self.err_message("Warning: Object cannot be rotated")

    def thread_for_rotate(self, images, cwise):
        """ Rotate all image files in an extra thread """
        try:
            to_reload = []
            for image in images:
                im = Image.open(image)
                if cwise == 1:
                    im = im.transpose(Image.ROTATE_90)
                elif cwise == 2:
                    im = im.transpose(Image.ROTATE_180)
                elif cwise == 3:
                    im = im.transpose(Image.ROTATE_270)
                self.save_image(im, image)
                to_reload.append([image, self.paths.index(image)])
            if self.thumbnail_toggled:
                for image in to_reload:
                    self.thumb_reload(image[0], image[1])
        except:
            self.err_message("Error: Rotation of file failed")

    def flip(self, dir):
        try:
            dir = int(dir)
            images = self.manipulated_images("Flipped")
            # Flip the image shown
            if self.paths[self.index] in images:
                self.pixbufOriginal = self.pixbufOriginal.flip(dir)
                self.update_image(False)
            # Flip all files in an extra thread
            flip_thread = Thread(target=self.thread_for_flip, args=(images,
                                                                    dir))
            flip_thread.start()
        except:
            self.err_message("Warning: Object cannot be flipped")

    def thread_for_flip(self, images, dir):
        """ Flip all image files in an extra thread """
        try:
            for image in images:
                im = Image.open(image)
                if dir:
                    im = im.transpose(Image.FLIP_LEFT_RIGHT)
                else:
                    im = im.transpose(Image.FLIP_TOP_BOTTOM)
                self.save_image(im, image)
                if self.thumbnail_toggled:
                    self.thumb_reload(image, self.paths.index(image))
        except:
            self.err_message("Error: Flipping of file failed")

    def rotate_auto(self):
        """ This function autorotates all pictures in the current pathlist """
        rotated_images = 0
        # jhead does this better
        try:
            cmd = ["jhead", "-autorot", "-ft"] + self.paths
            p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            out = out.decode(encoding='UTF-8')
            err = err.decode(encoding='UTF-8')
            # Find out how many images were rotated
            for line in out.split("\n"):
                if "Modified" in line and line.split()[1] not in err:
                    rotated_images += 1
            # Added to the message displayed when done
            method = "jhead"
        # If it isn't there fall back to PIL
        except:
            for path in self.paths:
                im = Image.open(path)
                exif = im._getexif()
                orientation_key = 274  # cf ExifTags
                rotated = True

                # Only do something if orientation info is there
                if exif and orientation_key in exif:
                    orientation = exif[orientation_key]
                    # Rotate and save the image
                    if orientation == 3:
                        im = im.transpose(Image.ROTATE_180)
                    elif orientation == 6:
                        im = im.transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        im = im.transpose(Image.ROTATE_90)
                    else:
                        rotated = False
                    if rotated:
                        self.save_image(im, path)
                        rotated_images += 1
                method = "PIL"
        # Reload current image and display a message if something was done
        if rotated_images:
            self.move_index(True, False, 0)
            message = "Autorotated %d image(s) using %s." % (rotated_images,
                                                             method)
        else:
            message = "No image rotated. Tried using %s." % (method)
        self.err_message(message)

    def manipulate(self):
        """ Starts a toolbar with basic image manipulation """
        # A vbox in which everything gets packed
        self.hboxman = Gtk.HBox(spacing=5)
        self.hboxman.connect("key_press_event", self.handle_key_press,
                             "MANIPULATE")

        # A list to save the changes being done
        self.manipulations = [1, 1, 1, False]

        # Sliders
        self.scale_bri = Gtk.HScale()
        self.scale_bri.connect("value-changed", self.value_slider, "bri")
        self.scale_con = Gtk.HScale()
        self.scale_con.connect("value-changed", self.value_slider, "con")
        self.scale_sha = Gtk.HScale()
        self.scale_sha.connect("value-changed", self.value_slider, "sha")

        # Set some properties
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            scale.set_range(-127, 127)
            scale.set_size_request(120, 20)
            scale.set_value(0)
            scale.set_digits(0)

        # Labels
        bri_label = Gtk.Label()
        bri_label.set_markup("\n<b>Bri</b>")
        con_label = Gtk.Label()
        con_label.set_markup("\n<b>Con</b>")
        sha_label = Gtk.Label()
        sha_label.set_markup("\n<b>Sha</b>")

        # Buttons
        button_yes = Gtk.Button(label="Accept")
        button_yes.connect("clicked", self.button_clicked, True)
        button_yes.set_size_request(80, 20)
        button_no = Gtk.Button(label="Cancel")
        button_no.connect("clicked", self.button_clicked, False)
        button_no.set_size_request(80, 20)
        button_opt = Gtk.Button(label="Optimize")
        button_opt.connect("clicked", self.button_opt_clicked)
        button_opt.set_size_request(80, 20)

        # Pack everything into the box
        for item in [bri_label, self.scale_bri, con_label, self.scale_con,
                     sha_label, self.scale_sha, button_opt, button_yes,
                     button_no]:
            self.hboxman.add(item)

    def manipulate_toggle(self):
        if self.manipulate_toggled:
            self.manipulate_toggled = False
            self.hboxman.hide()
            self.scrolled_win.grab_focus()
            self.update_info()
        elif self.paths and not(self.thumbnail_toggled or self.library_focused):
            try:
                self.pixbufOriginal.is_static_image()
                self.err_message("Manipulating Gifs is not supported")
            except:
                self.manipulate_toggled = True
                self.hboxman.show()
                self.scale_bri.grab_focus()
                self.update_info()
        else:
            if self.thumbnail_toggled:
                self.err_message("Manipulate not supported in thumbnail mode")
            elif self.library_focused:
                self.err_message("Manipulate not supported in library")
            else:
                self.err_message("No image open to edit")

    def manipulate_image(self, real=""):
        """ Apply the actual changes defined by the following actions """
        if real:  # To the actual image?
            orig, out = real, real
        # A thumbnail for higher responsiveness
        elif "-EDIT" not in self.paths[self.index]:
            im = Image.open(self.paths[self.index])
            out = "-EDIT.".join(self.paths[self.index].rsplit(".", 1))
            orig = out.replace("EDIT", "EDIT-ORIG")
            im.thumbnail(self.imsize, Image.ANTIALIAS)
            self.save_image(im, out)
            self.paths[self.index] = out
            # Save the original to work with
            self.save_image(im, orig)
        else:
            out = self.paths[self.index]
            orig = out.replace("EDIT", "EDIT-ORIG")
        # Apply all manipulations
        if self.manipulations[3]:  # Optimize
            try:
                Popen(["mogrify", "-contrast", "-auto-gamma", "-auto-level",
                       orig], shell=False).communicate()
            except:
                err = "Optimize exited with status 1, is imagemagick installed?"
                self.err_message(err)
                return
        im = Image.open(orig)
        # Enhance all three values
        im = ImageEnhance.Brightness(im).enhance(self.manipulations[0])
        im = ImageEnhance.Contrast(im).enhance(self.manipulations[1])
        im = ImageEnhance.Sharpness(im).enhance(self.manipulations[2])
        # Write
        self.save_image(im, out)

        # Show the edited image
        self.image.clear()
        self.pixbufOriginal = GdkPixbuf.PixbufAnimation.new_from_file(out)
        self.pixbufOriginal = self.pixbufOriginal.get_static_image()
        if not self.fullscreen_toggled:
            self.imsize = self.image_size()
        self.zoom_percent = self.get_zoom_percent()
        self.update_image()

    def value_slider(self, slider, name):
        """ Function for the brightness/contrast sliders """
        val = slider.get_value()
        val = (val + 127) / 127
        # Change brightness, contrast or sharpness
        if name == "bri":
            self.manipulations[0] = val
        elif name == "con":
            self.manipulations[1] = val
        else:
            self.manipulations[2] = val
        # Run the manipulation function
        self.manipulate_image()

    def focus_slider(self, man):
        """ Focuses one of the three sliders """
        if man == "bri":
            self.scale_bri.grab_focus()
        elif man == "con":
            self.scale_con.grab_focus()
        else:
            self.scale_sha.grab_focus()

    def change_slider(self, dec, large):
        """ Changes the value of the currently focused slider """
        for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
            if scale.is_focus():
                val = scale.get_value()
                if self.num_str:
                    step = int(self.num_str)
                    self.num_str = ""
                elif large:
                    step = 10
                else:
                    step = 1
                if dec:
                    val -= step
                else:
                    val += step
                scale.set_value(val)

    def button_clicked(self, widget, accept=False):
        """ Finishes manipulate mode """
        # Reload the real images if changes were made
        if "EDIT" in self.paths[self.index]:
            out = self.paths[self.index]             # manipulated thumbnail
            orig = out.replace("EDIT", "EDIT-ORIG")  # original thumbnail
            path = out.replace("-EDIT", "")          # real file
            # Edit the actual file if yes
            if accept:
                self.manipulate_image(path)
            # Reset all the manipulations
            self.manipulations = [1, 1, 1, False]
            for scale in [self.scale_bri, self.scale_con, self.scale_sha]:
                scale.set_value(0)
            # Remove the thumbnail files used
            os.remove(out)
            os.remove(orig)
            # Show the original image
            self.image.clear()
            self.pixbufOriginal = GdkPixbuf.PixbufAnimation.new_from_file(path)
            self.pixbufOriginal = self.pixbufOriginal.get_static_image()
            self.paths[self.index] = path
            if not self.fullscreen_toggled:
                self.imsize = self.image_size()
            self.zoom_percent = self.get_zoom_percent()
            self.update_image()
        # Done
        self.manipulate_toggle()
        self.update_info()

    def button_opt_clicked(self, widget):
        """ Sets optimize to True and runs the manipulation """
        self.manipulations[3] = True
        self.manipulate_image()

    def animation_toggle(self):
        if self.paths and not self.thumbnail_toggled:
            self.animation_toggled = not self.animation_toggled
            self.update_image()

    def thumbnails(self):
        imlist = []

        # Create thumbnail directory if necessary
        thumbdir = os.path.expanduser("~/.vimiv/Thumbnails")
        if not os.path.isdir(thumbdir):
            os.mkdir(thumbdir)
        # Get all thumbnails
        thumbnails = os.listdir(thumbdir)

        self.errorpos = []  # Catch errors to focus images correctly later
        # Create thumbnails for all images in the path
        for i, infile in enumerate(self.paths):
            outfile = ".".join(infile.split(".")[:-1]) + ".thumbnail" + ".png"
            outfile = outfile.split("/")[-1]
            outfile = os.path.join(thumbdir, outfile)
            # Only if they aren't cached already
            if outfile.split("/")[-1] not in thumbnails:
                try:
                    im = Image.open(infile)
                    im.thumbnail(self.thumbsize, Image.ANTIALIAS)
                    self.save_image(im, outfile)
                    imlist.append(outfile)
                except:
                    err = "Error: thumbnail creation for " + outfile + " failed"
                    self.err_message(err)
                    self.errorpos.append(i)
            else:
                imlist.append(outfile)

        # Create the liststore and iconview
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconview = Gtk.IconView.new()
        self.iconview.connect("item-activated", self.iconview_clicked)
        self.iconview.connect("key_press_event", self.handle_key_press,
                              "THUMBNAIL")
        self.iconview.set_model(self.liststore)
        self.columns = int(self.imsize[0]/(self.thumbsize[0]+30))
        self.iconview.set_spacing(0)
        self.iconview.set_columns(self.columns)
        self.iconview.set_item_width(5)
        self.iconview.set_item_padding(10)
        self.iconview.set_pixbuf_column(0)
        self.iconview.set_border_width(1)
        self.iconview.set_markup_column(1)

        # Add all thumbnails to the liststore
        for i, thumb in enumerate(imlist):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(thumb)
            name = thumb.split("/")[-1].split(".")[0]
            if self.paths[i] in self.marked:
                name = name + " [*]"
            self.liststore.append([pixbuf, name])

        # Draw the icon view instead of the image
        self.viewport.remove(self.image)
        self.viewport.add(self.iconview)
        # Show the window
        self.iconview.show()
        self.thumbnail_toggled = True
        # Focus the current immage
        self.iconview.grab_focus()
        self.thumbpos = (self.index) % len(self.paths)
        for i in self.errorpos:
            if self.thumbpos > i:
                self.thumbpos -= 1
        curpath = Gtk.TreePath.new_from_string(str(self.thumbpos))
        self.iconview.select_path(curpath)
        curthing = self.iconview.get_cells()[0]
        self.iconview.set_cursor(curpath, curthing, False)

    def iconview_clicked(self, w, count):
        # Move to the current position if the iconview is clicked
        self.thumbnail_toggle()
        count = count.get_indices()[0] + 1
        self.num_clear()
        for i in self.errorpos:
            if count > i:
                count += 1
        self.num_str = str(count)
        self.move_pos()

    def thumbnail_toggle(self):
        if self.thumbnail_toggled:
            self.viewport.remove(self.iconview)
            self.viewport.add(self.image)
            self.update_image()
            self.scrolled_win.grab_focus()
            self.thumbnail_toggled = False
        elif self.paths:
            self.thumbnails()
            self.timer_id = GLib.timeout_add(1, self.scroll_to_thumb)
            if self.library_focused:
                self.treeview.grab_focus()
            if self.manipulate_toggled:
                self.manipulate_toggle()
        else:
            self.err_message("No open image")
        # Update info for the current mode
        self.update_info()

    def thumb_reload(self, thumb, index, reload_image=True):
        """ Reloads the thumbnail of manipulated images """
        for i in self.errorpos:
            if index > i:
                index -= 1
        iter = self.liststore.get_iter(index)
        self.liststore.remove(iter)
        try:
            # Recreate the thumbnail
            outfile = ".".join(thumb.split(".")[:-1]) + ".thumbnail" + ".png"
            outfile = outfile.split("/")[-1]
            thumbdir = os.path.expanduser("~/.vimiv/Thumbnails")
            outfile = os.path.join(thumbdir, outfile)
            if reload_image:
                im = Image.open(thumb)
                im.thumbnail(self.thumbsize)
                self.save_image(im, outfile)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(outfile)
            name = outfile.split("/")[-1].split(".")[0]
            if thumb in self.marked:
                name = name + " [*]"
            self.liststore.insert(index, [pixbuf, name])
            path = Gtk.TreePath.new_from_string(str(self.thumbpos))
            self.iconview.select_path(path)
            curthing = self.iconview.get_cells()[0]
            self.iconview.set_cursor(path, curthing, False)
        except:
            self.err_message("Reload of manipulated thumbnails failed ")

    def scroll_to_thumb(self):
        """ Function which scrolls to the currently selected thumbnail """
        # TODO
        scrollamount = int(self.thumbpos / self.columns) * self.thumbsize[1]
        Gtk.Adjustment.set_step_increment(
            self.viewport.get_vadjustment(), scrollamount)
        self.scrolled_win.emit('scroll-child',
                               Gtk.ScrollType.STEP_FORWARD, False)

    def get_zoom_percent(self, zWidth=False, zHeight=False):
        """ returns the current zoom factor """
        # Size of the file
        pboWidth = self.pixbufOriginal.get_width()
        pboHeight = self.pixbufOriginal.get_height()
        pboScale = pboWidth / pboHeight
        # Size of the image to be shown
        wScale = self.imsize[0] / self.imsize[1]
        stickout = zWidth | zHeight

        # Image is completely shown and user doesn't want overzoom
        if (pboWidth < self.imsize[0] and pboHeight < self.imsize[1] and
                not (stickout or self.overzoom)):
            return 1
        # "Portrait" image
        elif (pboScale < wScale and not stickout) or zHeight:
            return self.imsize[1] / pboHeight
        # "Panorama/landscape" image
        else:
            return self.imsize[0] / pboWidth

    def update_image(self, update_info=True, update_gif=True):
        """ Show the final image """
        if not self.paths:
            return
        pboWidth = self.pixbufOriginal.get_width()
        pboHeight = self.pixbufOriginal.get_height()

        try:  # If possible scale the image
            pbfWidth = int(pboWidth * self.zoom_percent)
            pbfHeight = int(pboHeight * self.zoom_percent)
            # Rescaling of svg
            ending = self.paths[self.index].split("/")[-1].split(".")[-1]
            if ending == "svg" and self.rescale_svg:
                pixbufFinal = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    self.paths[self.index], -1, pbfHeight, True)
            else:
                pixbufFinal = self.pixbufOriginal.scale_simple(
                    pbfWidth, pbfHeight, GdkPixbuf.InterpType.BILINEAR)
            self.image.set_from_pixbuf(pixbufFinal)
        except:  # If not it must me an animation
            # TODO actual pause and play of Gifs
            self.zoom_percent = 1
            if update_gif:
                if not self.animation_toggled:
                    self.image.set_from_animation(self.pixbufOriginal)
                else:
                    pixbufFinal = self.pixbufOriginal.get_static_image()
                    self.image.set_from_pixbuf(pixbufFinal)
        # Update the statusbar if required
        if update_info:
            self.update_info()

    def update_info(self):
        """ Update the statusbar and the window title """
        # Left side
        try:
            # Directory if library is focused
            if self.library_focused:
                self.left_label.set_text(os.path.abspath("."))
            # Position, name and thumbnail size in thumb mode
            elif self.thumbnail_toggled:
                name = self.paths[self.thumbpos].split("/")[-1]
                message = "{0}/{1}  {2}  {3}".format(self.thumbpos+1,
                    len(self.paths), name, self.thumbsize)
                self.left_label.set_text(message)
            # Image info in image mode
            else:
                name = self.paths[self.index].split("/")[-1]
                message = "{0}/{1}  {2}  [{3:.0f}%]".format(self.index+1,
                    len(self.paths), name, self.zoom_percent*100)
                self.left_label.set_text(message)
        except:
            self.left_label.set_text("No open images")
        # Center
        if not (self.thumbnail_toggled or self.library_focused) and self.paths:
            mark = "[*]" if self.paths[self.index] in self.marked else ""
        else:
            mark = ""
        if self.slideshow:
            slideshow = "[slideshow - {0:.1f}s]".format(self.slideshow_delay)
        else:
            slideshow = ""
        message = "{0}  {1}".format(mark, slideshow)
        self.center_label.set_text(message)
        # Right side
        mode = self.get_mode()
        message = "{0:15}  {1:4}".format(mode, self.num_str)
        self.right_label.set_markup(message)
        # Window title
        try:
            name = self.paths[self.index].split("/")[-1]
            self.set_title("vimiv - "+name)
        except:
            self.set_title("vimiv")
        # Size of statusbar for resizing image
        self.statusbar_size = self.labelbox.get_allocated_height()

    def get_mode(self):
        """ Returns which widget is currently focused """
        if self.library_focused:
            return "<b>-- LIBRARY --</b>"
        elif self.manipulate_toggled:
            return "<b>-- MANIPULATE --</b>"
        elif self.thumbnail_toggled:
            return "<b>-- THUMBNAIL --</b>"
        else:
            return "<b>-- IMAGE --</b>"

    def image_size(self):
        """ Returns the size of the image depending on what other widgets
        are visible and if fullscreen or not """
        if self.fullscreen_toggled:
            size = self.screensize
        else:
            size = self.get_size()
        if self.library_toggled:
            size = (size[0] - self.library_width, size[1])
        if not self.sbar:
            size = (size[0], size[1] - self.statusbar_size - 24)
        return size

    def zoom_delta(self, delta):
        """ Zooms the image by delta percent """
        if self.thumbnail_toggled:
            return
        try:
            self.zoom_percent = self.zoom_percent * (1 + delta)
            # Catch some unreasonable zooms
            if (self.pixbufOriginal.get_height()*self.zoom_percent < 5 or
                    self.pixbufOriginal.get_height()*self.zoom_percent >
                    self.screensize[0]*5):
                raise ValueError
            self.user_zoomed = True
            self.update_image(update_gif=False)
        except:
            self.zoom_percent = self.zoom_percent / (1 + delta)
            self.err_message("Warning: Object cannot be zoomed (further)")

    def zoom_to(self, percent, zWidth=False, zHeight=False):
        """ Zooms to a given percentage """
        if self.thumbnail_toggled:
            return
        before = self.zoom_percent
        self.user_zoomed = False
        # Catch user zooms
        if self.num_str:
            self.user_zoomed = True
            percent = self.num_str
            # If prefixed with a zero invert value
            try:
                if percent[0] == "0":
                    percent = 1/float(percent[1:])
                else:
                    percent = float(percent)
            except:
                self.err_message("Error: Zoom percentage not parseable")
                return
            self.num_str = ""
        try:
            self.imsize = self.image_size()
            self.zoom_percent = (percent if percent
                                 else self.get_zoom_percent(zWidth, zHeight))
            # Catch some unreasonable zooms
            if (self.pixbufOriginal.get_height()*self.zoom_percent < 5 or
                    self.pixbufOriginal.get_height()*self.zoom_percent >
                    self.screensize[0]*5):
                self.zoom_percent = before
                raise ValueError
            self.update_image(update_gif=False)
        except:
            self.err_message("Warning: Object cannot be zoomed (further)")

    def center_window(self):
        """ Centers the image in the current window """
        # Don't do anything if no images are open
        if not self.paths or self.thumbnail_toggled:
            return
        # Vertical
        pboHeight = self.pixbufOriginal.get_height()
        vadj = self.viewport.get_vadjustment().get_value()
        vact = self.zoom_percent * pboHeight
        diff = vact - self.imsize[1]
        if diff > 0:
            toscroll = (diff - 2*vadj) / 2
            Gtk.Adjustment.set_step_increment(
                self.viewport.get_vadjustment(), toscroll)
            self.scrolled_win.emit('scroll-child',
                                   Gtk.ScrollType.STEP_FORWARD, False)
            # Reset scrolling
            Gtk.Adjustment.set_step_increment(self.viewport.get_vadjustment(),
                                              100)
        # Horizontal
        pboWidth = self.pixbufOriginal.get_width()
        hadj = self.viewport.get_hadjustment().get_value()
        hact = self.zoom_percent * pboWidth
        if diff > 0:
            diff = hact - self.imsize[0]
            toscroll = (diff - 2*hadj) / 2
            Gtk.Adjustment.set_step_increment(
                self.viewport.get_hadjustment(), toscroll)
            self.scrolled_win.emit('scroll-child',
                                   Gtk.ScrollType.STEP_FORWARD, True)
            # Reset scrolling
            Gtk.Adjustment.set_step_increment(self.viewport.get_hadjustment(),
                                              100)

    def move_index(self, forward=True, key=False, delta=1, force=False):
        """ Move by delta in the path """
        # Check if an image is opened
        if not self.paths or self.thumbnail_toggled:
            return
        # Check if image has been edited
        if self.check_for_edit(force):
            return
        # Check for prepended numbers
        if key and self.num_str:
            delta *= int(self.num_str)
        # Forward or backward
        if not forward:
            delta *= -1
        self.index = (self.index + delta) % len(self.paths)
        self.user_zoomed = False

        # Reshuffle on wrap-around
        if self.shuffle and self.index is 0 and delta > 0:
            shuffle(self.paths)

        path = self.paths[self.index]
        try:
            if not os.path.exists(path):
                print("Error: Couldn't open", path)
                self.delete()
                return
            else:
                self.pixbufOriginal = GdkPixbuf.PixbufAnimation.new_from_file(
                    path)
            if self.pixbufOriginal.is_static_image():
                self.pixbufOriginal = self.pixbufOriginal.get_static_image()
                self.imsize = self.image_size()
                self.zoom_percent = self.get_zoom_percent()
            else:
                self.zoom_percent = 1
            # If one simply reloads the file the info shouldn't be updated
            if delta:
                self.update_image()
            else:
                self.update_image(False)

        except GLib.Error:  # File not accessible
            self.paths.remove(path)
            self.err_message("Error: file not accessible")
            self.move_pos(False)

        self.num_clear()
        return True  # for the slideshow

    def move_pos(self, forward=True, force=False):
        """ Move to pos in path """
        # Check if image has been edited (might be gone by now -> try)
        try:
            if self.check_for_edit(force):
                raise ValueError
        except:
            return
        max = len(self.paths)
        if self.thumbnail_toggled:
            current = self.thumbpos % len(self.paths)
            max = max - len(self.errorpos)
        else:
            current = (self.index) % len(self.paths)
        # Move to definition by keys or end/beg
        if self.num_str:
            pos = int(self.num_str)
        elif forward:
            pos = max
        else:
            pos = 1
        # Catch exceptions
        try:
            current = int(current)
            max = int(max)
            if pos < 0 or pos > max:
                raise ValueError
        except:
            self.err_message("Warning: Unsupported index")
            return False
        # Do the math and move
        dif = pos - current - 1
        if self.thumbnail_toggled:
            pos -= 1
            self.thumbpos = pos
            path = Gtk.TreePath.new_from_string(str(pos))
            self.iconview.select_path(path)
            curthing = self.iconview.get_cells()[0]
            self.iconview.set_cursor(path, curthing, False)
            if forward:
                self.scrolled_win.emit('scroll-child',
                                       Gtk.ScrollType.END, False)
            else:
                self.scrolled_win.emit('scroll-child',
                                       Gtk.ScrollType.START, False)
        else:
            self.move_index(True, False, dif)
            self.user_zoomed = False

        self.num_clear()
        return True

    def num_append(self, num):
        """ Adds a new char to the num_str """
        self.num_str += num
        self.timer_id = GLib.timeout_add_seconds(1, self.num_clear)
        self.update_info()

    def num_clear(self):
        """ Clears the num_str """
        self.num_str = ""
        self.update_info()

    def recursive_search(self, dir):
        """ Searchs a given directory recursively for images """
        self.paths = self.filelist_create(dir)
        for path in self.paths:
            path = os.path.join(dir, path)
            if os.path.isfile(path):
                self.paths.append(path)
            else:
                self.recursive_search(path)

    def mark(self):
        """ Marks the current image """
        # Check which image
        if self.library_focused:
            current = os.path.abspath(self.files[self.treepos])
        elif self.thumbnail_toggled:
            index = self.thumbpos
            pathindex = index
            # Remove errors and reload the thumb_name
            for i in self.errorpos:
                if pathindex >= i:
                    pathindex += 1
            current = self.paths[pathindex]
        else:
            current = self.paths[self.index]
        # Toggle the mark
        if os.path.isfile(current):
            if current in self.marked:
                self.marked.remove(current)
            else:
                self.marked.append(current)
            self.mark_reload(False, [current])
        else:
            self.err_message("Marking directories is not supported")

    def mark_toggle(self):
        if self.marked:
            self.marked_bak = self.marked
            self.marked = []
        else:
            self.marked, self.marked_bak = self.marked_bak, self.marked
        to_reload = self.marked + self.marked_bak
        self.mark_reload(False, to_reload)

    def mark_all(self):
        """ Marks all images """
        # Get the correct filelist
        if self.library_focused:
            files = []
            for fil in self.files:
                files.append(os.path.abspath(fil))
        elif self.paths:
            files = self.paths
        else:
            self.err_message("No image to mark")
        # Add all to the marks
        for fil in files:
            if os.path.isfile(fil) and fil not in self.marked:
                self.marked.append(fil)
        self.mark_reload()

    def mark_between(self):
        """ Marks all images between the two last selections """
        # Check if there are enough marks
        if len(self.marked) < 2:
            self.err_message("Not enough marks")
            return
        start = self.marked[-2]
        end = self.marked[-1]
        # Get the correct filelist
        if self.library_focused:
            files = []
            for fil in self.files:
                files.append(os.path.abspath(fil))
        elif self.paths:
            files = self.paths
        else:
            self.err_message("No image to mark")
        # Find the images to mark
        for i, image in enumerate(files):
            if image == start:
                start = i
            elif image == end:
                end = i
        for i in range(start+1, end):
            self.marked.insert(-1, files[i])
        self.mark_reload()

    def mark_reload(self, all=True, current=None):
        self.update_info()
        # Update lib
        if self.library_toggled:
            self.remember_pos(".", self.treepos)
            self.reload(".")
            self.update_info()
        if self.thumbnail_toggled:
            for i, image in enumerate(self.paths):
                if all or image in current:
                    self.thumb_reload(image, i, False)

    def library(self):
        """ Starts the library browser """
        # Librarybox
        self.boxlib = Gtk.HBox()
        # Set up the self.grid in which the file info will be positioned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        if self.paths or not self.expand_lib:
            self.grid.set_size_request(self.library_width-self.border_width, 10)
        else:
            self.grid.set_size_request(self.winsize[0], 10)
        # A simple border
        if self.border_width:
            border = Gtk.Box()
            border.set_size_request(self.border_width, 0)
            border.modify_bg(Gtk.StateType.NORMAL, self.border_color)
            self.boxlib.pack_end(border, False, False, 0)
        # Entering content
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 4, 10)
        # Pack everything
        self.boxlib.pack_start(self.grid, True, True, 0)
        # Call the function to create the treeview
        self.treeview_create()
        self.scrollable_treelist.add(self.treeview)

    def library_toggle(self):
        """ Toggles the library """
        if self.library_toggled:
            self.remember_pos(os.path.abspath("."), self.treepos)
            self.boxlib.hide()
            self.animation_toggled = False  # Now play Gifs
            self.library_toggled = not self.library_toggled
            self.library_focus(False)
        else:
            self.boxlib.show()
            if not self.paths:
                self.scrolled_win.hide()
            else:  # Try to focus the current image in the library
                path = self.paths[self.index].split("/")[:-1]
                path = "/".join(path)
                if path == os.path.abspath("."):
                    self.treeview.set_cursor(Gtk.TreePath([self.index]),
                                             None, False)
                    self.treepos = self.index
            self.animation_toggled = True  # Do not play Gifs with the lib
            self.library_toggled = not self.library_toggled
            self.library_focus(True)
            # Markings and other stuff might have changed
            self.reload(os.path.abspath("."))
        if not self.user_zoomed and self.paths:
            self.zoom_to(0)  # Always rezoom the image
        #  Change the toggle state of animation
        self.update_image()

    def library_focus(self, library=True):
        if library:
            if not self.library_toggled:
                self.library_toggle()
            self.treeview.grab_focus()
            self.library_focused = True
        else:
            self.scrolled_win.grab_focus()
            self.library_focused = False
        # Update info for the current mode
        self.update_info()

    def treeview_create(self):
        # Tree View
        current_file_filter = self.filestore(self.datalist_create())
        self.treeview = Gtk.TreeView.new_with_model(current_file_filter)
        # Needed for the movement keys
        self.treepos = 0
        self.treeview.set_enable_search(False)
        # Select file when row activated
        self.treeview.connect("row-activated", self.file_select, True)
        # Handle key events
        self.treeview.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.treeview.connect("key_press_event", self.handle_key_press,
                              "LIBRARY")
        # Add the columns
        for i, name in enumerate(["Num", "Name", "Size", "M"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(name, renderer, markup=i)
            if name == "Name":
                column.set_expand(True)
                column.set_max_width(20)
            self.treeview.append_column(column)

    def filestore(self, datalist):
        """ Returns the file_filter for the tree view """
        # Filelist in a liststore model
        self.filelist = Gtk.ListStore(int, str, str, str)
        # Numerate each filename
        count = 0
        for data in datalist:
            count += 1
            data.insert(0, count)
            # The data into the filelist
            self.filelist.append(data)

        current_file_filter = self.filelist.filter_new()
        return current_file_filter

    def datalist_create(self):
        """ Returns the list of data for the file_filter model """
        self.datalist = list()
        self.files = self.filelist_create()
        # Remove unsupported files if one isn't in the tagdir
        if os.path.abspath(".") != tagdir:
            self.files = [
                possible_file
                for possible_file in self.files
                if (mimetypes.guess_type(possible_file)[0] in types or
                    os.path.isdir(possible_file))]
        # Add all the supported files
        for fil in self.files:
            size = self.filesize[fil]
            marked = ""
            if os.path.abspath(fil) in self.marked:
                marked = "[*]"
            if os.path.isdir(fil):
                fil = "<b>" + fil + "</b>"
            self.datalist.append([fil, size, marked])

        return self.datalist

    def filelist_create(self, dir="."):
        """ Create a filelist from all files in dir """
        # Get data from ls -lh and parse it correctly
        if self.show_hidden:
            p = Popen(['ls', '-lAh', dir], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen(['ls', '-lh', dir], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        data, err = p.communicate()
        data = data.decode(encoding='UTF-8').split("\n")[1:-1]
        files = []
        self.filesize = {}
        for fil in data:
            fil = fil.split()
            # Catch stupid filenames with whitespaces
            filename = " ".join(fil[8:])
            files.append(filename)
            # Number of images in dir as filesize
            if os.path.isdir(filename):
                try:
                    subfiles = os.listdir(filename)
                    subfiles = [
                        possible_file
                        for possible_file in subfiles
                        if mimetypes.guess_type(possible_file)[0] in types]
                    self.filesize[filename] = str(len(subfiles))
                except:
                    self.filesize[filename] = "N/A"
            else:
                self.filesize[filename] = fil[4]

        return files

    def file_select(self, alternative, count, b, close):
        """ Focus image or open dir for activated file in library """
        if isinstance(count, str):
            fil = count
        else:
            count = count.get_indices()[0]
            fil = self.files[count]
            self.remember_pos(os.path.abspath("."), count)
        # Catch symbolic links
        if "->" in fil:
            fil = "".join(fil.split(">")[:-1]).split(" ")[:-1]
            fil = "".join(fil)
            fil = os.path.realpath(fil)
            self.move_up(os.path.dirname(fil))
        # Tags
        if os.path.abspath(".") == tagdir:
            self.tag_load(fil)
            return
        # Rest
        if os.path.isdir(fil):  # Open the directory
            self.move_up(fil)
        else:  # Focus the image and populate a new list from the dir
            if self.paths and fil in self.paths[self.index]:
                close = True  # Close if file selected twice
            path = 0  # Reload the path, could have changed (symlinks)
            for f in self.files:
                if f == fil:
                    break
                else:
                    path += 1
            self.treeview.set_cursor(Gtk.TreePath(path), None, False)
            self.treepos = path
            self.paths, self.index = populate(self.files)
            # Show the selected file, if thumbnail toggled go out
            if self.thumbnail_toggled:
                self.thumbnail_toggle()
                self.treeview.grab_focus()
            self.move_index(True, False, count)
            # Close the library depending on key and repeat
            if close:
                self.library_toggle()
                self.update_image()

    def move_up(self, dir="..", start=False):
        """ move (up/to) dir in the library """
        try:
            curdir = os.path.abspath(".")
            os.chdir(dir)
            if not start:
                self.reload(os.path.abspath("."), curdir)
        except:
            self.err_message("Error: directory not accessible")

    def remember_pos(self, dir, count):
        self.dir_pos[dir] = count

    def reload(self, dir, curdir=""):
        """ Reloads the treeview """
        self.scrollable_treelist.remove(self.treeview)
        self.treeview_create()
        self.scrollable_treelist.add(self.treeview)
        self.library_focus(True)
        # Check if there is a saved position
        if dir in self.dir_pos.keys():
            self.treeview.set_cursor(Gtk.TreePath(self.dir_pos[dir]),
                                     None, False)
            self.treepos = self.dir_pos[dir]
        # Check if the last directory is in the current one
        else:
            curdir = curdir.split("/")[-1]
            for i, fil in enumerate(self.files):
                if curdir == fil:
                    self.treeview.set_cursor(Gtk.TreePath([i]), None, False)
                    self.treepos = i
                    break
        self.boxlib.show_all()

    def move_pos_lib(self, forward=True):
        """ Move to pos in lib """
        max = len(self.files) - 1
        if self.num_str:
            pos = int(self.num_str) - 1
            if pos < 0 or pos > max:
                self.err_message("Warning: Unsupported index")
                return False
        elif forward:
            pos = max
        else:
            pos = 0
        try:
            self.treepos = pos
            self.treeview.set_cursor(Gtk.TreePath(self.treepos), None, False)
        except:
            self.err_message("Warning: Unsupported index")
            return False

        self.num_clear()
        return True

    def resize_lib(self, val=None, inc=True):
        """ Resize the library and update the image if necessary """
        if isinstance(val, int):
            # The default 0 passed by arguments
            if not val:
                val = 300
            self.library_width = self.library_default_width
        elif val:  # A non int was given as library width
            self.err_message("Library width must be an integer")
            return
        elif inc:
            self.library_width += 20
        else:
            self.library_width -= 20
        # Set some reasonable limits to the library size
        if self.library_width > self.winsize[0]-200:
            self.library_width = self.winsize[0]-200
        elif self.library_width < 100:
            self.library_width = 100
        self.grid.set_size_request(self.library_width-self.border_width, 10)
        # Rezoom image
        if not self.user_zoomed and self.paths:
            self.zoom_to(0)

    def hidden_toggle(self):
        self.show_hidden = not self.show_hidden
        self.reload('.')

    def tag_load(self, name):
        """ Load all images in tag 'name' as current filelist """
        # Read file and get all tagged images as list
        os.chdir(tagdir)
        filename = os.path.join(tagdir, name)
        tagged_images = []
        try:
            tagfile = open(filename, 'r')
            for line in tagfile:
                tagged_images.append(line.rstrip("\n"))
        except:
            self.err_message("Tagfile %s does not exist" % (filename))
            return
        # Populate filelist
        self.paths = []
        self.paths = populate(tagged_images)
        if self.paths:
            self.scrolled_win.show()
            self.move_index(False, False, 0)
            # Close library if necessary
            if self.library_toggled:
                self.library_toggle()
        else:
            err = "Tagfile '%s' has no valid images" % (name)
            self.err_message(err)

    def tag_write(self, name):
        """ Append marked images to the tag 'name' """
        # Open the file checking for content
        filename = os.path.join(tagdir, name)
        tagged_images = []
        if os.path.isfile(filename):
            tagfile = open(filename, 'r')
            for line in tagfile:
                tagged_images.append(line.rstrip("\n"))
        tagfile = open(filename, 'a')
        # Write each marked image to the file if it isn't there
        for im in self.marked:
            if im not in tagged_images:
                tagfile.write(im + "\n")

    def tag_remove(self, name):
        """ Remove tag 'name' """
        filename = os.path.join(tagdir, name)
        if os.path.isfile(filename):
            os.remove(filename)
        else:
            self.err_message("Tagfile %s does not exist" % (filename))

    def auto_resize(self, w):
        """ Automatically resize image when window is resized """
        if self.get_size() != self.winsize:
            self.winsize = self.get_size()
            if self.paths and not self.user_zoomed:
                self.zoom_to(0)
            elif not self.paths and self.expand_lib:
                self.grid.set_size_request(self.winsize[0], 10)
            self.cmd_line_info.set_max_width_chars(self.winsize[0]/16)

    def cmd_handler(self, entry):
        """ Handles input from the entry, namely if it is a path to be focused
        or a (external) command to be run """
        # cmd from input
        command = entry.get_text()
        # And close the cmd line
        self.cmd_line_leave()
        if command[0] == "/":  # Search
            self.search(command.lstrip("/"))
        else:  # Run a command
            cmd = command.lstrip(":")
            # If there was no command just leave
            if not cmd:
                return
            # Parse different starts
            if cmd[0] == "!":
                self.run_external_command(cmd)
            elif cmd[0] == "~" or cmd[0] == "." or cmd[0] == "/":
                self.cmd_path(cmd)
            else:
                self.num_str = ""  # Be able to repeat commands
                while True:
                    try:
                        num = int(cmd[0])
                        self.num_str = self.num_str + str(num)
                        cmd = cmd[1:]
                    except:
                        break
                self.run_command(cmd)
        # Save the cmd to a list
        if command in self.cmd_history:
            self.cmd_history.remove(command)
        self.cmd_history.insert(0, command)
        self.cmd_pos = 0

    def run_external_command(self, cmd):
        """ Run the entered command in the terminal """
        # Check on which file(s) % and * should operate
        if self.last_focused == "lib" and self.files:
            filelist = self.files
            fil = self.files[self.treepos]
        elif self.paths:
            filelist = self.paths
            fil = self.paths[self.index]
        else:
            filelist = []
            fil = ""
        if self.marked:  # Always operate on marked files if they exist
            filelist = self.marked
        # Escape spaces for the shell
        fil = fil.replace(" ", "\\\\\\\\ ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace(" ", "\\\\\\\\ ")
        cmd = cmd[1:]
        # Substitute % and * with escaping
        cmd = re.sub(r'(?<!\\)(%)', fil, cmd)
        cmd = re.sub(r'(?<!\\)(\*)', " ".join(filelist), cmd)
        cmd = re.sub(r'(\\)(?!\\)', '', cmd)
        # Run the command in an extra thread
        dir = os.path.abspath(".")
        cmd_thread = Thread(target=self.thread_for_external, args=(cmd, dir))
        cmd_thread.start()
        # Undo the escaping
        fil = fil.replace("\\\\\\\\ ", " ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace("\\\\\\\\ ", " ")

    def thread_for_external(self, cmd, dir):
        """ Starting a new thread for external commands """
        try:
            # Possibility to "pipe to vimiv"
            if cmd[-1] == "|":
                cmd = cmd.rstrip("|")
                p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
                pipe = True
            else:
                p = Popen(cmd, stderr=PIPE, shell=True)
                pipe = False
            # Get output and error and run the command
            out, err = p.communicate()
            if p.returncode:
                err = err.decode('utf-8').split("\n")[0]
                self.err_message(err)
            else:
                GLib.timeout_add(1, self.reload_changes, dir, True, pipe, out)
            # Reload everything after an external command if we haven't moved,
            # you never know what happend ...
            # Must be in a timer because not all Gtk stuff can be accessed from
            # an external thread
        except FileNotFoundError as e:
            e = str(e)
            cmd = e.split()[-1]
            self.err_message("Command %s not found" % (cmd))

    def reload_changes(self, dir, reload_path=True, pipe=False, input=None):
        """ Reload everything, meaning filelist in library and image """
        if (dir == os.path.abspath(".") and dir != tagdir and
                self.library_toggled):
            if self.treepos >= 0 and self.treepos <= len(self.files):
                self.remember_pos(dir, self.treepos)
            self.reload(dir)
        if self.paths and reload_path:
            pathdir = os.path.dirname(self.paths[self.index])
            files = sorted(os.listdir(pathdir))
            for i, fil in enumerate(files):
                files[i] = os.path.join(pathdir, fil)
            self.num_str = str(self.index + 1)  # Remember current pos
            self.paths = []
            self.paths = populate(files)
            self.move_pos()
            if self.expand_lib and not self.paths:
                self.grid.set_size_request(self.winsize[0], 10)
            if self.thumbnail_toggled:
                for i, image in self.paths:
                    self.thumb_reload(image, i, False)
        # Run the pipe
        if pipe:
            self.pipe(input)
        return False  # To stop the timer

    def pipe(self, input):
        """ Run output of external command in a pipe
            This checks for directories, files and vimiv commands """
        # Leave if no input came
        if not input:
            self.err_message("No input from pipe")
            return
        # Make the input a file
        input = input.decode('utf-8')
        input = input.split("\n")[:-1]  # List of commands without empty line
        startout = input[0]
        # Do different stuff depending on the first line of input
        if os.path.isdir(startout):
            self.move_up(startout)
        elif os.path.isfile(startout):
            # Remember oldfile if no image was in filelist
            if self.paths:
                old_pos = [self.paths[self.index]]
                self.paths = []
            else:
                old_pos = []
            # Populate filelist
            self.paths = populate(input)
            if self.paths:  # Images were found
                self.scrolled_win.show()
                self.move_index(False, False, 0)
                # Close library if necessary
                if self.library_toggled:
                    self.library_toggle()
            elif old_pos:  # Nothing found, go back
                self.paths = populate(old_pos)
                self.err_message("No image found")
        else:
            # Run every line as an internal command
            for cmd in input:
                self.run_command(cmd)

    def cmd_path(self, path):
        """ Run a path command, namely populate files or focus directory """
        # Expand home
        if path[0] == "~":
            path = os.path.expanduser("~") + path[1:]
        try:
            path = os.path.abspath(path)
            if not os.path.exists(path):
                raise ValueError
            elif os.path.isdir(path):
                self.move_up(path)
                # If we open the library it must be focused as well
                self.last_focused = "lib"
            else:
                # If it is an image open it
                self.paths = []
                self.paths = populate([path])
                self.move_index(True, False, 0)
                #  Reload library in lib mode, do not open it in image mode
                abspath = os.path.dirname(path)
                if self.last_focused == "lib":
                    self.last_selected = path
                    self.move_up(abspath)
                    # Focus it in the treeview so it can be accessed via "l"
                    for i, fil in enumerate(self.files):
                        if fil in path:
                            self.treeview.set_cursor(Gtk.TreePath(i),
                                                     None, False)
                            self.treepos = i
                            break
                else:
                    self.move_up(abspath, True)
        except:
            self.err_message("Warning: Not a valid path")

    def run_command(self, cmd):
        """ Run the correct internal cmd """
        parts = cmd.split()
        if "set" in cmd:
            arg = parts[2:]
            cmd = " ".join(parts[:2])
        else:
            arg = parts[1:]
            cmd = parts[0]
        # Check if the command exists
        if cmd in self.commands.keys():  # Run it
            function = self.commands[cmd][0]
            default_args = self.commands[cmd][1:]
            arg = default_args + arg
            # Check for wrong arguments
            try:
                if arg:
                    function(*arg)
                else:
                    function()
            except TypeError as e:
                self.err_message(str(e))
            except SyntaxError:
                err = ("SyntaxError: are all strings closed " +
                       "and special chars quoted?")
                self.err_message(err)
            except NameError as e:
                argstr = "('" + arg + "')"
                arg = "(" + arg + ")"
                function = function.replace(arg, argstr)
                exec(function)
        else:  # Through an error
            self.err_message("No such command: %s" % (cmd))

    def history(self, down):
        """ Update the cmd_handler text with history """
        # Shortly disconnect the change signal
        self.cmd_line.disconnect_by_func(self.cmd_check_close)
        # Only parts of the history that match the entered text
        if not self.sub_history:
            substring = self.cmd_line.get_text()
            matchstr = '^(' + substring + ')'
            self.sub_history = [substring]
            for cmd in self.cmd_history:
                if re.match(matchstr, cmd):
                    self.sub_history.append(cmd)
        # Move and set the text
        if down:
            self.cmd_pos -= 1
        else:
            self.cmd_pos += 1
        self.cmd_pos = self.cmd_pos % (len(self.sub_history))
        self.cmd_line.set_text(self.sub_history[self.cmd_pos])
        self.cmd_line.set_position(-1)
        # Reconnect when done
        self.cmd_line.connect("changed", self.cmd_check_close)

    def cmd_line_focus(self):
        """ Open and focus the command line """
        # Colon for text
        self.cmd_line.set_text(":")
        # Show the statusbar
        if self.sbar:
            self.leftbox.show()
        # Remove old error messages
        self.update_info()
        # Show/hide the relevant stuff
        self.cmd_line_box.show()
        self.labelbox.hide()
        self.leftbox.set_border_width(10)
        # Remember what widget was focused before
        if self.library_focused:
            self.last_focused = "lib"
        elif self.manipulate_toggled:
            self.last_focused = "man"
        elif self.thumbnail_toggled:
            self.last_focused = "thu"
        else:
            self.last_focused = "im"
        self.cmd_line.grab_focus()
        self.cmd_line.set_position(-1)

    def cmd_line_leave(self):
        """ Close the command line """
        self.cmd_line_box.hide()
        self.labelbox.show()
        self.leftbox.set_border_width(12)
        # Remove all completions shown and the text currently inserted
        self.cmd_line_info.set_text("")
        self.cmd_line.set_text("")
        # Refocus the remembered widget
        if self.last_focused == "lib":
            self.library_focus(True)
        elif self.last_focused == "man":
            self.scale_bri.grab_focus()
        elif self.last_focused == "thu":
            self.iconview.grab_focus()
        else:
            self.scrolled_win.grab_focus()
        # Rehide the command line
        if self.sbar:
            self.leftbox.hide()

    def cmd_check_close(self, entry):
        """ Close the entry if the colon/slash is deleted """
        self.sub_history = []
        self.cmd_pos = 0
        text = entry.get_text()
        if not text or text[0] not in ":/":
            self.cmd_line_leave()

    def cmd_complete(self):
        """ Simple autocompletion for the command line """
        command = self.cmd_line.get_text()
        command = command.lstrip(":")
        # Strip prepending numbers
        numstr = ""
        while True:
            try:
                num = int(command[0])
                numstr += str(num)
                command = command[1:]
            except:
                break
        completions = []
        commandlist = sorted(list(self.commands.keys()))

        # Check if the first part is a shell command or a path
        comp_type = "int"
        if command:
            if command[0] == "!":
                comp_type = "ext"
                # Check if path completion would be useful
                if len(command.split()) > 1:
                    if command.split()[-1][0] != "-":
                        comp_type = "path"
                        # Path to be completed is last argument
                        path = command.split()[-1]
                        files = self.cmd_complete_path(path, True)
                        # Command is everything ahead
                        cmd = " ".join(command.split()[:-1])
                        commandlist = []
                        # Join both for a commandlist
                        for fil in files:
                            commandlist.append(cmd + " " + fil)
                        commandlist = sorted(commandlist)
                else:
                    commandlist = external_commands
            # Path
            elif command[0] == "/" or command[0] == "~" or command[0] == ".":
                comp_type = "path"
                commandlist = sorted(self.cmd_complete_path(command))

        # Tag completion
        if comp_type == "int":
            if re.match(r'^(tag_(write|remove|load) )', command):
                tags = os.listdir(os.path.expanduser("~/.vimiv/Tags"))
                commandlist = []
                for tag in tags:
                    commandlist.append(command.split()[0] + " " + tag)
                comp_type = "tag"  # Chop the command in the info

        # Check if the entered text matches the beginning of a command
        for cmd in commandlist:
            matchstr = '^(' + command + ')'
            if re.match(matchstr, cmd):
                completions.append(cmd)

        if completions:
            # Reinsert the prepending numbers
            output = numstr
            # If there is only one completion insert it
            if len(completions) == 1:
                output += completions[0]
                self.cmd_line_info.set_text("")
            # Else complete until last equal character and show all completions
            else:
                first = completions[0]
                last = completions[-1]
                # Only show the filename if completing self.paths
                if comp_type == "path":
                    for i, comp in enumerate(completions):
                        if comp.endswith("/"):
                            completions[i] = comp.split("/")[-2] + "/"
                        else:
                            completions[i] = comp.split("/")[-1]
                elif comp_type == "tag":  # And only the tags if completing tags
                    for i, comp in enumerate(completions):
                        completions[i] = " ".join(comp.split()[1:])
                # A string with possible completions for the info
                compstr = "  " + "  ".join(completions)
                self.cmd_line_info.set_text(compstr)
                # Find last equal character
                for i, char in enumerate(first):
                    if char == last[i]:
                        output += char
                    else:
                        break
            output = ":" + output
            self.cmd_line.set_text(output)
            self.cmd_line.set_position(-1)
        else:
            self.cmd_line_info.set_text("  No matching completion")

        return True  # Deactivates default bindings (here for Tab)

    def cmd_complete_path(self, path, command=False):
        """ Completion for files in a specific path """
        # Directory of the path
        dir = "/".join(path.split("/")[:-1])
        if not dir:
            dir = path[0]
            if not os.path.exists(os.path.expanduser(dir)):
                dir = "."
        # Get entries
        if self.show_hidden:
            files = sorted(os.listdir(dir))
        else:
            files = sorted(self.listdir_nohidden(dir))
        # Format them neatly depending on directory and type
        filelist = []
        for fil in files:
            if dir != "." or not command:
                fil = os.path.join(dir, fil)
            # Directory
            if os.path.isdir(os.path.expanduser(fil)):
                filelist.append(fil + "/")
            # Acceptable file
            elif mimetypes.guess_type(fil)[0] in types or command:
                filelist.append(fil)
        return filelist

    def clear(self, dir):
        """ Remove all files in dir (Trash or Thumbnails) """
        trashdir = os.path.join(os.path.expanduser("~/.vimiv"), dir)
        for fil in os.listdir(trashdir):
            fil = os.path.join(trashdir, fil)
            os.remove(fil)

    def cmd_edit(self, man, num="0"):
        """ Run the specified edit command """
        if not self.manipulate_toggled:
            if not self.paths:
                self.err_message("No image to manipulate")
                return
            else:
                self.manipulate_toggle()
        if man == "opt":
            self.button_opt_clicked("button_widget")
        else:
            self.focus_slider(man)
            self.num_str = num
            execstr = "self.scale_" + man + ".set_value(int(self.num_str))"
            exec(execstr)
        self.num_str = ""

    def cmd_search(self):
        """ Prepend search to the cmd_line and open it """
        self.cmd_line_focus()
        self.cmd_line.set_text("/")
        self.cmd_line.set_position(-1)

    def search(self, searchstr):
        """ Run a search on the appropriate filelist """
        if self.library_focused:
            for i, fil in enumerate(self.files):
                if searchstr in fil:
                    self.file_select("alt", fil, "b", False)
                    return
        else:
            for i, fil in enumerate(self.paths):
                if searchstr in fil:
                    print(fil)
                    self.num_str = str(i+1)
                    self.move_pos()
                    return
        # Nothing found
        self.err_message("No matching file")

    def listdir_nohidden(self, path):
        """ Reimplementation of os.listdir which doesn't show hidden files """
        files = os.listdir(os.path.expanduser(path))
        for fil in files:
            if not fil.startswith("."):
                yield fil

    def format_files(self, string):
        if not self.paths:
            self.err_message("No files in path")
            return

        # Check if exifdata is available and needed
        tofind = ("%" in string)
        if tofind:
            try:
                for fil in self.paths:
                    im = Image.open(fil)
                    exif = im._getexif()
                    if not (exif and 306 in exif):
                        raise AttributeError
            except:
                self.err_message("No exif data for %s available" % (fil))
                return

        for i, fil in enumerate(self.paths):
            ending = fil.split(".")[-1]
            num = "%03d" % (i+1)
            # Exif stuff
            if tofind:
                im = Image.open(fil)
                exif = im._getexif()
                date = exif[306]
                time = date.split()[1].split(":")
                date = date.split()[0].split(":")
                outstring = string.replace("%Y", date[0])  # year
                outstring = outstring.replace("%m", date[1])  # month
                outstring = outstring.replace("%d", date[2])  # day
                outstring = outstring.replace("%H", time[0])  # hour
                outstring = outstring.replace("%M", time[1])  # minute
                outstring = outstring.replace("%S", time[2])  # second
            else:
                outstring = string
            # Ending
            outstring += num + "." + ending
            shutil.move(fil, outstring)

        # Reload everything
        self.reload_changes(os.path.abspath("."), True)

    def handle_key_press(self, widget, event, window):
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        shiftkeys = ["space", "Return", "Tab", "Escape", "BackSpace",
                     "Up", "Down", "Left", "Right"]
        # Check for Control (^), Mod1 (Alt) or Shift
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            keyname = "^" + keyname
        if event.get_state() & Gdk.ModifierType.MOD1_MASK:
            keyname = "Alt+".format(keyname)
        # Shift+ for all letters and for keys that don't support it
        if (event.get_state() & Gdk.ModifierType.SHIFT_MASK and
                (len(keyname) < 2 or keyname in shiftkeys)):
            keyname = "Shift+" + keyname.lower()
        try:  # Numbers for the num_str
            if window == "COMMAND":
                raise ValueError
            int(keyname)
            self.num_append(keyname)
            return True
        except:
            try:
                # Get the relevant keybindings for the window from the various
                # sections in the keys.conf file
                keys = self.keys[window]
                if window in ["IMAGE", "THUMBNAIL", "LIBRARY"]:
                    keys.update(self.keys["GENERAL"])
                if window in ["IMAGE", "THUMBNAIL"]:
                    keys.update(self.keys["IM_THUMB"])
                if window in ["IMAGE", "LIBRARY"]:
                    keys.update(self.keys["IM_LIB"])

                # Get the command to which the pressed key is bound
                func = keys[keyname]
                if "set " in func:
                    conf_args = []
                else:
                    func = func.split()
                    conf_args = func[1:]
                    func = func[0]
                # From functions dictionary get the actual vimiv command
                func = self.functions[func]
                args = func[1:]
                args.extend(conf_args)
                func = func[0]
                func(*args)
                return True  # Deactivates default bindings
            except:
                return False

    def main(self):
        # Move to the directory of the image
        if self.paths:
            os.chdir(os.path.dirname(self.paths[self.index]))

        # Screen
        screen = Gdk.Screen()
        self.screensize = [screen.width(), screen.height()]

        # Gtk window with general settings
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('destroy', Gtk.main_quit)
        self.connect("check-resize", self.auto_resize)
        self.set_icon_name("image-x-generic")

        # Box in which everything gets packed
        self.vbox = Gtk.VBox()
        # Horizontal Box with image and treeview
        self.hbox = Gtk.HBox(False, 0)
        self.add(self.vbox)
        # Scrollable window for the image
        self.scrolled_win = Gtk.ScrolledWindow()
        self.hbox.pack_end(self.scrolled_win, True, True, 0)
        self.vbox.pack_start(self.hbox, True, True, 0)

        # Viewport
        self.viewport = Gtk.Viewport()
        self.viewport.set_shadow_type(Gtk.ShadowType.NONE)
        self.scrolled_win.add(self.viewport)
        self.image = Gtk.Image()
        self.viewport.add(self.image)
        self.scrolled_win.connect("key_press_event",
                                  self.handle_key_press, "IMAGE")
        # Command line
        self.cmd_line_box = Gtk.HBox(False, 0)
        self.cmd_line = Gtk.Entry()
        self.cmd_line.connect("activate", self.cmd_handler)
        self.cmd_line.connect("key_press_event",
                              self.handle_key_press, "COMMAND")
        self.cmd_line.connect("changed", self.cmd_check_close)
        self.cmd_line_info = Gtk.Label()
        self.cmd_line_info.set_max_width_chars(self.winsize[0]/16)
        self.cmd_line_info.set_ellipsize(Pango.EllipsizeMode.END)
        self.cmd_line_box.pack_start(self.cmd_line, True, True, 0)
        self.cmd_line_box.pack_end(self.cmd_line_info, False, False, 0)

        # Statusbar on the bottom
        self.labelbox = Gtk.HBox(False, 0)
        # Two labels for two sides of statusbar and one in the middle for
        # additional info
        self.left_label = Gtk.Label()  # Position and image name
        self.left_label.set_justify(Gtk.Justification.LEFT)
        self.right_label = Gtk.Label()  # Mode and prefixed numbers
        self.right_label.set_justify(Gtk.Justification.RIGHT)
        self.center_label = Gtk.Label()  # Zoom, marked, slideshow, ...
        self.center_label.set_justify(Gtk.Justification.CENTER)
        self.labelbox.pack_start(self.left_label, False, False, 0)
        self.labelbox.pack_start(self.center_label, True, True, 0)
        self.labelbox.pack_end(self.right_label, False, False, 0)

        # Box with the statusbar and the command line
        self.leftbox = Gtk.VBox(False, 0)
        self.leftbox.pack_start(self.labelbox, False, False, 0)
        self.leftbox.pack_end(self.cmd_line_box, False, False, 0)
        self.leftbox.set_border_width(12)
        self.vbox.pack_end(self.leftbox, False, False, 0)

        # Size for resizing image
        self.statusbar_size = self.labelbox.get_allocated_height()

        # Treeview
        self.library()
        self.hbox.pack_start(self.boxlib, False, False, 0)

        # Manipulate Bar
        self.manipulate()
        self.vbox.pack_end(self.hboxman, False, False, 0)

        # Set the window size
        self.resize(self.winsize[0], self.winsize[1])
        if self.fullscreen_toggled:
            self.fullscreen()

        self.show_all()
        # Hide the manipulate bar and the command line
        self.hboxman.hide()
        self.cmd_line_box.hide()

        # Show images, if a path was given
        if self.paths:
            self.move_index(True, False, 0)
            # Show library at the beginning?
            if self.library_toggled:
                self.boxlib.show()
            else:
                self.boxlib.hide()
            self.scrolled_win.grab_focus()
            if self.fullscreen_toggled:
                self.fullscreen()
            # Start in slideshow mode?
            if self.slideshow:
                self.slideshow = False
                self.toggle_slideshow()
            self.toggle_statusbar()
        else:
            self.slideshow = False  # Slideshow without self.paths makes no sense
            self.toggle_statusbar()
            self.library_focus(True)
            if self.expand_lib:
                self.grid.set_size_request(self.winsize[0], 10)
            self.err_message("No valid self.paths, opening library viewer")

        # Finally show the main window
        Gtk.main()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Vimiv().main()
