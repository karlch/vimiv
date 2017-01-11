# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
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
        # Structure:
        # Command name:
        # [function, [default args], [positional args], [optional args],
        #  supports_count]
        self.app.commands = {
            "accept_changes": [self.app["manipulate"].button_clicked,
                               [None, True], [], [], False],
            "alias": [self.app["commandline"].alias,
                      [], ["name", "command"], [], False],
            "autorotate": [self.app["manipulate"].rotate_auto,
                           [], [], [], False],
            "center": [self.app["image"].center_window, [], [], [], False],
            "clear_trash": [self.app["fileextras"].clear,
                            ['Trash'], [], [], False],
            "clear_thumbs": [self.app["fileextras"].clear,
                             ['Thumbnails'], [], [], False],
            "copy_basename": [self.app["fileextras"].copy_name,
                              [False], [], [], False],
            "copy_abspath": [self.app["fileextras"].copy_name,
                             [True], [], [], False],
            "delete": [self.app["manipulate"].delete, [], [], [], False],
            "discard_changes": [self.app["manipulate"].button_clicked,
                                [None, False], [], [], False],
            "first": [self.app["image"].move_pos, [False], [], [], True],
            "first_lib": [self.app["library"].move_pos, [False], [], [], True],
            "fit": [self.app["image"].zoom_to, [0], [], [], False],
            "fit_horiz": [self.app["image"].zoom_to, [0, 2], [], [], False],
            "fit_vert": [self.app["image"].zoom_to, [0, 3], [], [], False],
            "flip": [self.app["manipulate"].flip, [], ["direction"], [], False],
            "format": [self.app["fileextras"].format_files,
                       [], ["formatstring"], [], False],
            "fullscreen": [self.app["window"].toggle_fullscreen,
                           [], [], [], False],
            "grow_lib": [self.app["library"].resize,
                         [True, False], [], ["value"], True],
            "last": [self.app["image"].move_pos, [True], [], [], True],
            "last_lib": [self.app["library"].move_pos, [True], [], [], True],
            "library": [self.app["library"].toggle, [], [], [], False],
            "focus_library": [self.app["library"].focus,
                              [True], [], [], False],
            "unfocus_library": [self.app["library"].focus,
                                [False], [], [], False],
            "manipulate": [self.app["manipulate"].toggle, [], [], [], False],
            "mark": [self.app["mark"].mark, [], [], [], False],
            "mark_all": [self.app["mark"].mark_all, [], [], [], False],
            "mark_between": [self.app["mark"].mark_between, [], [], [], False],
            "mark_toggle": [self.app["mark"].toggle_mark, [], [], [], False],
            "move_up": [self.app["library"].move_up, [], [], [], True],
            "next": [self.app["image"].move_index, [True, True], [], [], True],
            "next!": [self.app["image"].move_index,
                      [True, True, 1, True], [], [], True],
            "prev": [self.app["image"].move_index, [False, True], [], [], True],
            "prev!": [self.app["image"].move_index,
                      [False, True, 1, True], [], [], True],
            "q": [self.app.quit_wrapper, [], [], [], False],
            "q!": [self.app.quit_wrapper, [True], [], [], False],
            "reload_lib": [self.app["library"].reload, ['.'], [], [], False],
            "rotate": [self.app["manipulate"].rotate, [], ["value"], [], True],
            "set animation!": [self.app["image"].toggle_animation,
                               [], [], [], False],
            "set brightness": [self.app["manipulate"].cmd_edit,
                               ['bri'], [], ["value"], False],
            "set clipboard!": [self.app["fileextras"].toggle_clipboard,
                               [], [], [], False],
            "set contrast": [self.app["manipulate"].cmd_edit,
                             ['con'], [], ["value"], False],
            "set library_width": [self.app["library"].resize,
                                  [None, True], [], ["value"], False],
            "set overzoom!": [self.app["image"].toggle_overzoom,
                              [], [], [], False],
            "set rescale_svg!": [self.app["image"].toggle_rescale_svg,
                                 [], [], [], False],
            "set sharpness": [self.app["manipulate"].cmd_edit,
                              ['sha'], [], ["value"], False],
            "set show_hidden!": [self.app["library"].toggle_hidden,
                                 [], [], [], False],
            "set slideshow_delay": [self.app["slideshow"].set_delay,
                                    [], [], ["value"], True],
            "set statusbar!": [self.app["statusbar"].toggle, [], [], [], False],
            "shrink_lib": [self.app["library"].resize,
                           [False, False], [], ["value"], True],
            "slideshow": [self.app["slideshow"].toggle, [], [], [], True],
            "slideshow_delay": [self.app["slideshow"].set_delay,
                                [None], ["value"], [], True],
            "tag_load": [self.app["tags"].load, [], ["tagname"], [], False],
            "tag_remove": [self.app["tags"].remove, [], ["tagname"], [], False],
            "tag_write": [self.app["tags"].write,
                          [self.app["mark"].marked], ["tagname"], [], False],
            "thumbnail": [self.app["thumbnail"].toggle, [], [], [], False],
            "version": [self.app["information"].show_version_info,
                        [], [], [], False],
            "zoom_in": [self.app["window"].zoom, [True], [], ["steps"], True],
            "zoom_out": [self.app["window"].zoom, [False], [], ["steps"], True],
            "zoom_to": [self.app["image"].zoom_to, [], ["percent"], [], True]}

        self.app.functions = {
            "clear_status": [self.app["statusbar"].clear_status,
                             [], [], [], False],
            "command": [self.app["commandline"].focus, [], [], ["text"], False],
            "complete": [self.app["completions"].complete,
                         [False], [], [], False],
            "complete_inverse": [self.app["completions"].complete,
                                 [True], [], [], False],
            "discard_command": [self.app["commandline"].leave,
                                [True], [], [], False],
            "focus_slider": [self.app["manipulate"].focus_slider,
                             [], ["name"], [], False],
            "history_down": [self.app["commandline"].history_search,
                             [True], [], [], False],
            "history_up": [self.app["commandline"].history_search,
                           [False], [], [], False],
            "scroll": [self.app["window"].scroll, [], ["direction"], [], True],
            "scroll_lib": [self.app["library"].scroll,
                           [], ["direction"], [], True],
            "search": [self.app["commandline"].cmd_search, [], [], [], False],
            "search_next": [self.app["commandline"].search_move,
                            [], [], [], True],
            "search_prev": [self.app["commandline"].search_move,
                            [False], [], [], True],
            "slider": [self.app["manipulate"].change_slider,
                       [], [], ["value"], True]}

        self.app.functions.update(self.app.commands)

        # Add aliases catching
        # 1) aliases that would overwrite an existing function
        # 2) aliases that link to a non-existing command
        self.app.aliases = \
            {alias: self.settings["ALIASES"][alias]
             for alias in self.settings["ALIASES"]
             if alias not in self.app.functions
             and (self.settings["ALIASES"][alias] in self.app.functions
                  or self.settings["ALIASES"][alias][0] in "~/.!")}

        # Generate completions as soon as commands exist
        self.app["completions"].generate_commandlist()
