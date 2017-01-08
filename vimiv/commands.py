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
        # [function, [default args], [positional args], [optional args]]
        self.app.commands = {
            "accept_changes": [self.app["manipulate"].button_clicked,
                               [None, True], [], []],
            "alias": [self.app["commandline"].alias,
                      [], ["name", "command"], []],
            "autorotate": [self.app["manipulate"].rotate_auto, [], [], []],
            "center": [self.app["image"].center_window, [], [], []],
            "clear_trash": [self.app["fileextras"].clear, ['Trash'], [], []],
            "clear_thumbs": [self.app["fileextras"].clear,
                             ['Thumbnails'], [], []],
            "copy_basename": [self.app["fileextras"].copy_name,
                              [False], [], []],
            "copy_abspath": [self.app["fileextras"].copy_name, [True], [], []],
            "delete": [self.app["manipulate"].delete, [], [], []],
            "discard_changes": [self.app["manipulate"].button_clicked,
                                [None, False], [], []],
            "first": [self.app["image"].move_pos, [False], [], []],
            "first_lib": [self.app["library"].move_pos, [False], [], []],
            "fit": [self.app["image"].zoom_to, [0], [], []],
            "fit_horiz": [self.app["image"].zoom_to, [0, 2], [], []],
            "fit_vert": [self.app["image"].zoom_to, [0, 3], [], []],
            "flip": [self.app["manipulate"].flip, [], ["direction"], []],
            "format": [self.app["fileextras"].format_files,
                       [], ["formatstring"], []],
            "fullscreen": [self.app["window"].toggle_fullscreen, [], [], []],
            "grow_lib": [self.app["library"].resize,
                         [True, False], [], ["value"]],
            "last": [self.app["image"].move_pos, [True], [], []],
            "last_lib": [self.app["library"].move_pos, [True], [], []],
            "library": [self.app["library"].toggle, [], [], []],
            "focus_library": [self.app["library"].focus, [True], [], []],
            "unfocus_library": [self.app["library"].focus, [False], [], []],
            "manipulate": [self.app["manipulate"].toggle, [], [], []],
            "mark": [self.app["mark"].mark, [], [], []],
            "mark_all": [self.app["mark"].mark_all, [], [], []],
            "mark_between": [self.app["mark"].mark_between, [], [], []],
            "mark_toggle": [self.app["mark"].toggle_mark, [], [], []],
            "move_up": [self.app["library"].move_up, [], [], []],
            "next": [self.app["image"].move_index, [True, True], [], []],
            "next!": [self.app["image"].move_index,
                      [True, True, 1, True], [], []],
            "prev": [self.app["image"].move_index, [False, True], [], []],
            "prev!": [self.app["image"].move_index,
                      [False, True, 1, True], [], []],
            "q": [self.app.quit_wrapper, [], [], []],
            "q!": [self.app.quit_wrapper, [True], [], []],
            "reload_lib": [self.app["library"].reload, ['.'], [], []],
            "rotate": [self.app["manipulate"].rotate, [], ["value"], []],
            "set animation!": [self.app["image"].toggle_animation, [], [], []],
            "set brightness": [self.app["manipulate"].cmd_edit,
                               ['bri'], [], ["value"]],
            "set clipboard!": [self.app["fileextras"].toggle_clipboard,
                               [], [], []],
            "set contrast": [self.app["manipulate"].cmd_edit,
                             ['con'], [], ["value"]],
            "set library_width": [self.app["library"].resize,
                                  [None, True], [], ["value"]],
            "set overzoom!": [self.app["image"].toggle_overzoom,
                              [], [], []],
            "set rescale_svg!": [self.app["image"].toggle_rescale_svg,
                                 [], [], []],
            "set sharpness": [self.app["manipulate"].cmd_edit,
                              ['sha'], [], ["value"]],
            "set show_hidden!": [self.app["library"].toggle_hidden, [], [], []],
            "set slideshow_delay": [self.app["slideshow"].set_delay,
                                    [], [], ["value"]],
            "set statusbar!": [self.app["statusbar"].toggle, [], [], []],
            "shrink_lib": [self.app["library"].resize,
                           [False, False], [], ["value"]],
            "slideshow": [self.app["slideshow"].toggle, [], [], []],
            "slideshow_delay": [self.app["slideshow"].set_delay,
                                [None], ["value"], []],
            "tag_load": [self.app["tags"].load, [], ["tagname"], []],
            "tag_remove": [self.app["tags"].remove, [], ["tagname"], []],
            "tag_write": [self.app["tags"].write,
                          [self.app["mark"].marked], ["tagname"], []],
            "thumbnail": [self.app["thumbnail"].toggle, [], [], []],
            "version": [self.app["information"].show_version_info, [], [], []],
            "zoom_in": [self.app["window"].zoom, [True], [], ["steps"]],
            "zoom_out": [self.app["window"].zoom, [False], [], ["steps"]],
            "zoom_to": [self.app["image"].zoom_to, [], ["percent"], []]}

        self.app.functions = {
            "clear_status": [self.app["statusbar"].clear_status, [], [], []],
            "command": [self.app["commandline"].focus, [], [], ["text"]],
            "complete": [self.app["completions"].complete, [False], [], []],
            "complete_inverse": [self.app["completions"].complete,
                                 [True], [], []],
            "discard_command": [self.app["commandline"].leave, [True], [], []],
            "focus_slider": [self.app["manipulate"].focus_slider,
                             [], ["name"], []],
            "history_down": [self.app["commandline"].history_search,
                             [True], [], []],
            "history_up": [self.app["commandline"].history_search,
                           [False], [], []],
            "scroll": [self.app["window"].scroll, [], ["direction"], []],
            "scroll_lib": [self.app["library"].scroll, [], ["direction"], []],
            "search": [self.app["commandline"].cmd_search, [], [], []],
            "search_next": [self.app["commandline"].search_move, [], [], []],
            "search_prev": [self.app["commandline"].search_move,
                            [False], [], []],
            "slider": [self.app["manipulate"].change_slider, [], [], ["value"]]}

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
