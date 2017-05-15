# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains all commands and functions for vimiv."""

from vimiv.tags import TagHandler


class Commands(object):
    """Create the commands for vimiv."""

    # Adding one command per statement is absolutely acceptable
    # pylint:disable=too-many-statements
    def __init__(self, app, settings):
        """Generate commands and functions.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
            commands: Dictionary containing all commands with information.
                See the add_command method.
        """
        self.app = app
        self.settings = settings
        self.commands = {}
        self.app["tag_handler"] = TagHandler(app)
        # Add all commands
        self.add_command("accept_changes",
                         self.app["manipulate"].finish,
                         default_args=[True])
        self.add_command("alias", self.app["commandline"].alias,
                         positional_args=["name", "command"])
        self.add_command("autorotate", self.app["manipulate"].rotate_auto)
        self.add_command("center", self.app["main_window"].center_window)
        self.add_command("copy_basename", self.app["fileextras"].copy_name,
                         default_args=[False])
        self.add_command("copy_abspath", self.app["fileextras"].copy_name,
                         default_args=[True])
        self.add_command("delete", self.app["manipulate"].delete)
        self.add_command("undelete", self.app["manipulate"].undelete,
                         positional_args=["basename"])
        self.add_command("discard_changes",
                         self.app["manipulate"].finish,
                         default_args=[False])
        self.add_command("first", self.app["image"].move_pos,
                         default_args=[False], supports_count=True)
        self.add_command("first_lib", self.app["library"].move_pos,
                         default_args=[False], supports_count=True)
        self.add_command("fit", self.app["image"].zoom_to,
                         default_args=[0])
        self.add_command("fit_horiz", self.app["image"].zoom_to,
                         default_args=[0, 2])
        self.add_command("fit_vert", self.app["image"].zoom_to,
                         default_args=[0, 3])
        self.add_command("flip", self.app["manipulate"].flip,
                         positional_args=["direction"])
        self.add_command("format", self.app["fileextras"].format_files,
                         positional_args=["formatstring"])
        self.add_command("fullscreen", self.app["window"].toggle_fullscreen)
        self.add_command("grow_lib", self.app["library"].resize,
                         default_args=[True, False], optional_args=["value"],
                         supports_count=True)
        self.add_command("last", self.app["image"].move_pos,
                         default_args=[True], supports_count=True)
        self.add_command("last_lib", self.app["library"].move_pos,
                         default_args=[True], supports_count=True)
        self.add_command("library", self.app["library"].toggle)
        self.add_command("focus_library", self.app["library"].focus,
                         default_args=[True])
        self.add_command("unfocus_library", self.app["library"].focus,
                         default_args=[False])
        self.add_command("manipulate", self.app["manipulate"].toggle)
        self.add_command("mark", self.app["mark"].mark)
        self.add_command("mark_all", self.app["mark"].mark_all)
        self.add_command("mark_between", self.app["mark"].mark_between)
        self.add_command("mark_toggle", self.app["mark"].toggle_mark)
        self.add_command("move_up", self.app["library"].move_up,
                         supports_count=True)
        self.add_command("next", self.app["image"].move_index,
                         default_args=[True, True], supports_count=True)
        self.add_command("next!", self.app["image"].move_index,
                         default_args=[True, True, 1, True],
                         supports_count=True)
        self.add_command("prev", self.app["image"].move_index,
                         default_args=[False, True], supports_count=True)
        self.add_command("prev!", self.app["image"].move_index,
                         default_args=[False, True, 1, True],
                         supports_count=True)
        self.add_command("q", self.app.quit_wrapper)
        self.add_command("q!", self.app.quit_wrapper,
                         default_args=[True])
        self.add_command("reload_lib", self.app["library"].reload,
                         default_args=["."])
        self.add_command("rotate", self.app["manipulate"].rotate,
                         positional_args=["value"], supports_count=True)
        self.add_command("set animation!", self.app["image"].toggle_animation)
        self.add_command("set brightness", self.app["manipulate"].cmd_edit,
                         default_args=["bri"], optional_args=["value"])
        self.add_command("set clipboard!",
                         self.app["fileextras"].toggle_clipboard)
        self.add_command("set contrast", self.app["manipulate"].cmd_edit,
                         default_args=["con"], optional_args=["value"])
        self.add_command("set library_width", self.app["library"].resize,
                         default_args=[None, True], optional_args=["value"])
        self.add_command("set overzoom", self.app["image"].set_overzoom,
                         optional_args=["value"])
        self.add_command("set rescale_svg!",
                         self.app["image"].toggle_rescale_svg)
        self.add_command("set sharpness", self.app["manipulate"].cmd_edit,
                         default_args=["sha"], optional_args=["value"])
        self.add_command("set show_hidden!", self.app["library"].toggle_hidden)
        self.add_command("set slideshow_delay", self.app["slideshow"].set_delay,
                         optional_args=["value"], supports_count=True)
        self.add_command("set statusbar!", self.app["statusbar"].toggle)
        self.add_command("shrink_lib", self.app["library"].resize,
                         default_args=[False, False], optional_args=["value"],
                         supports_count=True)
        self.add_command("slideshow", self.app["slideshow"].toggle,
                         supports_count=True)
        self.add_command("slideshow_delay", self.app["slideshow"].set_delay,
                         default_args=[None], positional_args=["value"],
                         supports_count=True)
        self.add_command("tag_load", self.app["tags"].load,
                         positional_args=["tagname"])
        self.add_command("tag_remove", self.app["tags"].remove,
                         positional_args=["tagname"])
        self.add_command("tag_write", self.app["tags"].write,
                         default_args=[self.app["mark"].marked],
                         positional_args=["tagname"])
        self.add_command("thumbnail", self.app["thumbnail"].toggle)
        self.add_command("version", self.app["information"].show_version_info)
        self.add_command("zoom_in", self.app["window"].zoom,
                         default_args=[True], optional_args=["steps"],
                         supports_count=True)
        self.add_command("zoom_out", self.app["window"].zoom,
                         default_args=[False], optional_args=["steps"],
                         supports_count=True)
        self.add_command("zoom_to", self.app["image"].zoom_to,
                         optional_args=["percent"], supports_count=True)
        # Hidden commands
        self.add_command("clear_status", self.app["statusbar"].clear_status,
                         is_hidden=True)
        self.add_command("command", self.app["commandline"].focus,
                         optional_args=["text"], is_hidden=True)
        self.add_command("complete", self.app["completions"].complete,
                         default_args=[False], is_hidden=True)
        self.add_command("complete_inverse", self.app["completions"].complete,
                         default_args=[True], is_hidden=True)
        self.add_command("discard_command", self.app["commandline"].leave,
                         default_args=[True], is_hidden=True)
        self.add_command("focus_slider", self.app["manipulate"].focus_slider,
                         positional_args=["name"], is_hidden=True)
        self.add_command("history_down", self.app["commandline"].history_search,
                         default_args=[True], is_hidden=True)
        self.add_command("history_up", self.app["commandline"].history_search,
                         default_args=[False], is_hidden=True)
        self.add_command("scroll", self.app["main_window"].scroll,
                         positional_args=["direction"], supports_count=True,
                         is_hidden=True)
        self.add_command("scroll_lib", self.app["library"].scroll,
                         positional_args=["direction"], supports_count=True,
                         is_hidden=True)
        self.add_command("search", self.app["commandline"].cmd_search,
                         is_hidden=True)
        self.add_command("search_next", self.app["commandline"].search_move,
                         supports_count=True, is_hidden=True)
        self.add_command("search_prev", self.app["commandline"].search_move,
                         default_args=[False], supports_count=True,
                         is_hidden=True)
        self.add_command("slider", self.app["manipulate"].change_slider,
                         optional_args=["value"], supports_count=True,
                         is_hidden=True)

        # Add aliases catching
        # 1) aliases that would overwrite an existing function
        # 2) aliases that link to a non-existing command
        self.app.aliases = \
            {alias: self.settings["ALIASES"][alias]
             for alias in self.settings["ALIASES"]
             if alias not in self.app.functions
             and (self.settings["ALIASES"][alias] in self.app.functions
                  or self.settings["ALIASES"][alias][0] in "~/.!")}

    def __getitem__(self, name):
        """Return the command corresponding to name.

        Args:
            name: The name of the command to access.
        Return:
            Dictionary of the command information.
        """
        if name in self.commands:
            return self.commands[name]
        return None

    def add_command(self, name, function, default_args=None,
                    positional_args=None, optional_args=None,
                    supports_count=False, is_hidden=False):
        """Add a command.

        Args:
            name: Name of the command.
            function: Function that the command should call.
            default_args: Default arguments to pass to the function.
            positional_args: Arguments that must be passed by the user.
            optional_args: Arguments that may be passed by the user.
            supports_count: If false, delete any num_str before running the
                command.
            is_hidden: If true, hide command from the command line.
        """
        command = {"function": function,
                   "default_args": default_args if default_args else [],
                   "positional_args":
                       positional_args if positional_args else [],
                   "optional_args": optional_args if optional_args else [],
                   "supports_count": supports_count,
                   "is_hidden": is_hidden}
        self.commands[name] = command
