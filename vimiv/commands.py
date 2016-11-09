#!/usr/bin/env python
# encoding: utf-8
"""Contains all commands and functions for vimiv."""
from vimiv.tags import TagHandler


class Commands(object):
    """Create the commands for vimiv."""

    def __init__(self, vimiv, settings):
        """Generate commands and functions.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv
        self.settings = settings
        self.vimiv.tag_handler = TagHandler(vimiv)

        # Dictionary with command names and the corresponding functions
        self.vimiv.commands = {
            "accept_changes": [self.vimiv.manipulate.button_clicked, "w", True],
            "alias": [self.vimiv.commandline.alias],
            "autorotate": [self.vimiv.manipulate.rotate_auto],
            "center": [self.vimiv.image.center_window],
            "clear_trash": [self.vimiv.fileextras.clear, 'Trash'],
            "clear_thumbs": [self.vimiv.fileextras.clear, 'Thumbnails'],
            "delete": [self.vimiv.manipulate.delete],
            "discard_changes": [self.vimiv.manipulate.button_clicked, "w",
                                False],
            "first": [self.vimiv.image.move_pos, False],
            "first_lib": [self.vimiv.library.move_pos, False],
            "fit": [self.vimiv.image.zoom_to, 0],
            "fit_horiz": [self.vimiv.image.zoom_to, 0, True, False],
            "fit_vert": [self.vimiv.image.zoom_to, 0, False, True],
            "flip": [self.vimiv.manipulate.flip],
            "format": [self.vimiv.fileextras.format_files],
            "fullscreen": [self.vimiv.window.toggle_fullscreen],
            "grow_lib": [self.vimiv.library.resize, True, False],
            "last": [self.vimiv.image.move_pos, True],
            "last_lib": [self.vimiv.library.move_pos, True],
            "library": [self.vimiv.library.toggle],
            "focus_library": [self.vimiv.library.focus, True],
            "unfocus_library": [self.vimiv.library.focus, False],
            "manipulate": [self.vimiv.manipulate.toggle],
            "mark": [self.vimiv.mark.mark],
            "mark_all": [self.vimiv.mark.mark_all],
            "mark_between": [self.vimiv.mark.mark_between],
            "mark_toggle": [self.vimiv.mark.toggle_mark],
            "move_up": [self.vimiv.library.move_up],
            "next": [self.vimiv.image.move_index, True, True],
            "next!": [self.vimiv.image.move_index, True, True, 1, True],
            "optimize": [self.vimiv.manipulate.cmd_edit, 'opt'],
            "prev": [self.vimiv.image.move_index, False, True],
            "prev!": [self.vimiv.image.move_index, False, True, 1, True],
            "q": [self.vimiv.quit],
            "q!": [self.vimiv.quit, True],
            "reload_lib": [self.vimiv.library.reload, '.'],
            "rotate": [self.vimiv.manipulate.rotate],
            "set animation!": [self.vimiv.image.toggle_animation],
            "set brightness": [self.vimiv.manipulate.cmd_edit, 'bri'],
            "set contrast": [self.vimiv.manipulate.cmd_edit, 'con'],
            "set library_width": [self.vimiv.library.resize, None, True],
            "set overzoom!": [self.vimiv.image.toggle_overzoom],
            "set rescale_svg!": [self.vimiv.image.toggle_rescale_svg],
            "set sharpness": [self.vimiv.manipulate.cmd_edit, 'sha'],
            "set show_hidden!": [self.vimiv.library.toggle_hidden],
            "set slideshow_delay": [self.vimiv.slideshow.set_delay],
            "set statusbar!": [self.vimiv.statusbar.toggle],
            "shrink_lib": [self.vimiv.library.resize, False, False],
            "slideshow": [self.vimiv.slideshow.toggle],
            "slideshow_inc": [self.vimiv.slideshow.set_delay, 2, "+"],
            "slideshow_dec": [self.vimiv.slideshow.set_delay, 2, "-"],
            "tag_load": [self.vimiv.tags.load],
            "tag_remove": [self.vimiv.tags.remove],
            "tag_write": [self.vimiv.tags.write, self.vimiv.mark.marked],
            "thumbnail": [self.vimiv.thumbnail.toggle],
            "zoom_in": [self.vimiv.image.zoom_delta, +.25],
            "zoom_out": [self.vimiv.image.zoom_delta, -.25],
            "zoom_to": [self.vimiv.image.zoom_to],
            "zoom_thumb_in": [self.vimiv.thumbnail.zoom, True],
            "zoom_thumb_out": [self.vimiv.thumbnail.zoom, False]}

        self.vimiv.aliases = self.settings["ALIASES"]

        self.vimiv.functions = {
            "bri_focus": [self.vimiv.manipulate.focus_slider, "bri"],
            "con_focus": [self.vimiv.manipulate.focus_slider, "con"],
            "sha_focus": [self.vimiv.manipulate.focus_slider, "sha"],
            "slider_dec": [self.vimiv.manipulate.change_slider, True, False],
            "slider_inc": [self.vimiv.manipulate.change_slider, False, False],
            "slider_dec_large": [self.vimiv.manipulate.change_slider, True,
                                 True],
            "slider_inc_large": [self.vimiv.manipulate.change_slider, False,
                                 True],
            "cmd_history_up": [self.vimiv.commandline.history_search, False],
            "cmd_history_down": [self.vimiv.commandline.history_search, True],
            "discard_command": [self.vimiv.commandline.leave],
            "complete": [self.vimiv.completions.complete],
            "complete_inverse": [self.vimiv.completions.complete, True],
            "down": [self.vimiv.keyhandler.scroll, "j"],
            "down_lib": [self.vimiv.library.scroll, "j"],
            "down_page": [self.vimiv.keyhandler.scroll, "J"],
            "left": [self.vimiv.keyhandler.scroll, "h"],
            "left_lib": [self.vimiv.library.scroll, "h"],
            "left_page": [self.vimiv.keyhandler.scroll, "H"],
            "right": [self.vimiv.keyhandler.scroll, "l"],
            "right_lib": [self.vimiv.library.scroll, "l"],
            "right_page": [self.vimiv.keyhandler.scroll, "L"],
            "up": [self.vimiv.keyhandler.scroll, "k"],
            "up_lib": [self.vimiv.library.scroll, "k"],
            "up_page": [self.vimiv.keyhandler.scroll, "K"],
            "search": [self.vimiv.commandline.cmd_search],
            "search_next": [self.vimiv.commandline.search_move],
            "search_prev": [self.vimiv.commandline.search_move, False],
            "command": [self.vimiv.commandline.focus]}

        self.vimiv.functions.update(self.vimiv.commands)
