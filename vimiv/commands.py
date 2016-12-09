#!/usr/bin/env python
# encoding: utf-8
"""Contains all commands and functions for vimiv."""
from vimiv.tags import TagHandler


class Commands(object):
    """Create the commands for vimiv."""

    def __init__(self, app, settings):
        """Generate commands and functions.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        self.app = app
        self.settings = settings
        self.app["tag_handler"] = TagHandler(app)

        # Dictionary with command names and the corresponding functions
        self.app.commands = {
            "accept_changes": [self.app["manipulate"].button_clicked, "w", True],
            "alias": [self.app["commandline"].alias],
            "autorotate": [self.app["manipulate"].rotate_auto],
            "center": [self.app["image"].center_window],
            "clear_trash": [self.app["fileextras"].clear, 'Trash'],
            "clear_thumbs": [self.app["fileextras"].clear, 'Thumbnails'],
            "delete": [self.app["manipulate"].delete],
            "discard_changes": [self.app["manipulate"].button_clicked, "w",
                                False],
            "first": [self.app["image"].move_pos, False],
            "first_lib": [self.app["library"].move_pos, False],
            "fit": [self.app["image"].zoom_to, 0],
            "fit_horiz": [self.app["image"].zoom_to, 0, True, False],
            "fit_vert": [self.app["image"].zoom_to, 0, False, True],
            "flip": [self.app["manipulate"].flip],
            "format": [self.app["fileextras"].format_files],
            "fullscreen": [self.app["window"].toggle_fullscreen],
            "grow_lib": [self.app["library"].resize, True, False],
            "last": [self.app["image"].move_pos, True],
            "last_lib": [self.app["library"].move_pos, True],
            "library": [self.app["library"].toggle],
            "focus_library": [self.app["library"].focus, True],
            "unfocus_library": [self.app["library"].focus, False],
            "manipulate": [self.app["manipulate"].toggle],
            "mark": [self.app["mark"].mark],
            "mark_all": [self.app["mark"].mark_all],
            "mark_between": [self.app["mark"].mark_between],
            "mark_toggle": [self.app["mark"].toggle_mark],
            "move_up": [self.app["library"].move_up],
            "next": [self.app["image"].move_index, True, True],
            "next!": [self.app["image"].move_index, True, True, 1, True],
            "optimize": [self.app["manipulate"].cmd_edit, 'opt'],
            "prev": [self.app["image"].move_index, False, True],
            "prev!": [self.app["image"].move_index, False, True, 1, True],
            "q": [self.app.quit_wrapper],
            "q!": [self.app.quit_wrapper, True],
            "reload_lib": [self.app["library"].reload, '.'],
            "rotate": [self.app["manipulate"].rotate],
            "set animation!": [self.app["image"].toggle_animation],
            "set brightness": [self.app["manipulate"].cmd_edit, 'bri'],
            "set contrast": [self.app["manipulate"].cmd_edit, 'con'],
            "set library_width": [self.app["library"].resize, None, True],
            "set overzoom!": [self.app["image"].toggle_overzoom],
            "set rescale_svg!": [self.app["image"].toggle_rescale_svg],
            "set sharpness": [self.app["manipulate"].cmd_edit, 'sha'],
            "set show_hidden!": [self.app["library"].toggle_hidden],
            "set slideshow_delay": [self.app["slideshow"].set_delay],
            "set statusbar!": [self.app["statusbar"].toggle],
            "shrink_lib": [self.app["library"].resize, False, False],
            "slideshow": [self.app["slideshow"].toggle],
            "slideshow_inc": [self.app["slideshow"].set_delay, 2, "+"],
            "slideshow_dec": [self.app["slideshow"].set_delay, 2, "-"],
            "tag_load": [self.app["tags"].load],
            "tag_remove": [self.app["tags"].remove],
            "tag_write": [self.app["tags"].write, self.app["mark"].marked],
            "thumbnail": [self.app["thumbnail"].toggle],
            "version": [self.app["information"].show_version_info],
            "zoom_in": [self.app["image"].zoom_delta, +.25],
            "zoom_out": [self.app["image"].zoom_delta, -.25],
            "zoom_to": [self.app["image"].zoom_to],
            "zoom_thumb_in": [self.app["thumbnail"].zoom, True],
            "zoom_thumb_out": [self.app["thumbnail"].zoom, False]}

        self.app.aliases = self.settings["ALIASES"]

        self.app.functions = {
            "bri_focus": [self.app["manipulate"].focus_slider, "bri"],
            "con_focus": [self.app["manipulate"].focus_slider, "con"],
            "sha_focus": [self.app["manipulate"].focus_slider, "sha"],
            "slider_dec": [self.app["manipulate"].change_slider, True, False],
            "slider_inc": [self.app["manipulate"].change_slider, False, False],
            "slider_dec_large": [self.app["manipulate"].change_slider, True,
                                 True],
            "slider_inc_large": [self.app["manipulate"].change_slider, False,
                                 True],
            "cmd_history_up": [self.app["commandline"].history_search, False],
            "cmd_history_down": [self.app["commandline"].history_search, True],
            "discard_command": [self.app["commandline"].leave],
            "complete": [self.app["completions"].complete],
            "complete_inverse": [self.app["completions"].complete, True],
            "down": [self.app["keyhandler"].scroll, "j"],
            "down_lib": [self.app["library"].scroll, "j"],
            "down_page": [self.app["keyhandler"].scroll, "J"],
            "left": [self.app["keyhandler"].scroll, "h"],
            "left_lib": [self.app["library"].scroll, "h"],
            "left_page": [self.app["keyhandler"].scroll, "H"],
            "right": [self.app["keyhandler"].scroll, "l"],
            "right_lib": [self.app["library"].scroll, "l"],
            "right_page": [self.app["keyhandler"].scroll, "L"],
            "up": [self.app["keyhandler"].scroll, "k"],
            "up_lib": [self.app["library"].scroll, "k"],
            "up_page": [self.app["keyhandler"].scroll, "K"],
            "search": [self.app["commandline"].cmd_search],
            "search_next": [self.app["commandline"].search_move],
            "search_prev": [self.app["commandline"].search_move, False],
            "command": [self.app["commandline"].focus]}

        self.app.functions.update(self.app.commands)
