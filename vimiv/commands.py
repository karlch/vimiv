# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains all commands and functions for vimiv."""

from vimiv.exceptions import (AliasError, StringConversionError, NotABoolean,
                              NotANumber, SettingNotFoundError)
from vimiv.fileactions import format_files
from vimiv.helpers import error_message
from vimiv.settings import settings
from vimiv.tags import TagHandler


class Commands(object):
    """Initialize and store the commands for vimiv.

    Commands are added via Commands.add_command() and can be received via
    Commands["command_name"].

    Attributes:
        aliases: Dictionary of stored aliases.

        _app: The main vimiv application to interact with.
        _commands: Dictionary of stored commands.
        _n: Integer for iterator.
    """

    # Adding one command per statement is absolutely acceptable
    # pylint:disable=too-many-statements
    def __init__(self, app):
        """Generate commands and functions.

        Args:
            app: The main vimiv application to interact with.
        """
        self._app = app
        self._commands = {}
        self.aliases = {}
        self._n = 0
        self._app["tag_handler"] = TagHandler(app)
        # Add all commands
        self.add_command("accept_changes",
                         self._app["manipulate"].finish,
                         default_args=[True])
        self.add_command("alias", self.add_alias,
                         positional_args=["name", "command"])
        self.add_command("autorotate", self._app["transform"].rotate_auto)
        self.add_command("center", self._app["main_window"].center_window)
        self.add_command("copy_basename", self._app["clipboard"].copy_name,
                         default_args=[False])
        self.add_command("copy_abspath", self._app["clipboard"].copy_name,
                         default_args=[True])
        self.add_command("delete", self._app["transform"].delete)
        self.add_command("undelete", self._app["transform"].undelete,
                         positional_args=["basename"])
        self.add_command("discard_changes",
                         self._app["manipulate"].finish,
                         default_args=[False])
        self.add_command("edit", self._app["manipulate"].cmd_edit,
                         positional_args=["manipulation"],
                         optional_args=["value"])
        self.add_command("first", self._app["image"].move_pos,
                         default_args=[False], supports_count=True)
        self.add_command("first_lib", self._app["library"].move_pos,
                         default_args=[False], supports_count=True)
        self.add_command("fit", self._app["image"].zoom_to,
                         default_args=[0, "fit"])
        self.add_command("fit_horiz", self._app["image"].zoom_to,
                         default_args=[0, "horizontal"])
        self.add_command("fit_vert", self._app["image"].zoom_to,
                         default_args=[0, "vertical"])
        self.add_command("flip", self._app["transform"].flip,
                         positional_args=["direction"])
        self.add_command("format", format_files, default_args=[self._app],
                         positional_args=["formatstring"])
        self.add_command("fullscreen", self._app["window"].toggle_fullscreen)
        self.add_command("last", self._app["image"].move_pos,
                         default_args=[True], supports_count=True)
        self.add_command("last_lib", self._app["library"].move_pos,
                         default_args=[True], supports_count=True)
        self.add_command("library", self._app["library"].toggle)
        self.add_command("focus_library", self._app["library"].focus,
                         default_args=[True])
        self.add_command("unfocus_library", self._app["library"].focus,
                         default_args=[False])
        self.add_command("manipulate", self._app["manipulate"].toggle)
        self.add_command("mark", self._app["mark"].mark)
        self.add_command("mark_all", self._app["mark"].mark_all)
        self.add_command("mark_between", self._app["mark"].mark_between)
        self.add_command("mark_toggle", self._app["mark"].toggle_mark)
        self.add_command("move_up", self._app["library"].move_up,
                         supports_count=True)
        self.add_command("next", self._app["image"].move_index,
                         default_args=[True, True], supports_count=True)
        self.add_command("next!", self._app["image"].move_index,
                         default_args=[True, True, 1, True],
                         supports_count=True)
        self.add_command("prev", self._app["image"].move_index,
                         default_args=[False, True], supports_count=True)
        self.add_command("prev!", self._app["image"].move_index,
                         default_args=[False, True, 1, True],
                         supports_count=True)
        self.add_command("q", self._app.quit_wrapper)
        self.add_command("q!", self._app.quit_wrapper,
                         default_args=[True])
        self.add_command("reload_lib", self._app["library"].reload,
                         default_args=["."])
        self.add_command("rotate", self._app["transform"].rotate,
                         positional_args=["value"], supports_count=True)
        self.add_command("set", self.set, positional_args=["setting"],
                         optional_args=["value"], supports_count=True)
        self.add_command("slideshow", self._app["slideshow"].toggle,
                         supports_count=True)
        self.add_command("tag_load", self._app["tags"].load,
                         positional_args=["tagname"])
        self.add_command("tag_remove", self._app["tags"].remove,
                         positional_args=["tagname"])
        self.add_command("tag_write", self._app["tags"].write,
                         default_args=[self._app["mark"].marked],
                         positional_args=["tagname"])
        self.add_command("thumbnail", self._app["thumbnail"].toggle)
        self.add_command("version", self._app["information"].show_version_info)
        self.add_command("w", self._app["transform"].write)
        self.add_command("wq", self._app["transform"].write,
                         default_args=[True])
        self.add_command("zoom_in", self._app["window"].zoom,
                         default_args=[True], optional_args=["steps"],
                         supports_count=True)
        self.add_command("zoom_out", self._app["window"].zoom,
                         default_args=[False], optional_args=["steps"],
                         supports_count=True)
        self.add_command("zoom_to", self._app["image"].zoom_to,
                         optional_args=["percent"], supports_count=True)
        # Hidden commands
        self.add_command("clear_status", self._app["statusbar"].clear_status,
                         is_hidden=True)
        self.add_command("command", self._app["commandline"].enter,
                         optional_args=["text"], is_hidden=True)
        self.add_command("complete", self._app["completions"].complete,
                         default_args=[False], is_hidden=True)
        self.add_command("complete_inverse", self._app["completions"].complete,
                         default_args=[True], is_hidden=True)
        self.add_command("discard_command", self._app["commandline"].leave,
                         default_args=[True], is_hidden=True)
        self.add_command("focus_slider", self._app["manipulate"].focus_slider,
                         positional_args=["name"], is_hidden=True)
        self.add_command("history_down",
                         self._app["commandline"].history_search,
                         default_args=[True], is_hidden=True)
        self.add_command("history_up", self._app["commandline"].history_search,
                         default_args=[False], is_hidden=True)
        self.add_command("scroll", self._app["main_window"].scroll,
                         positional_args=["direction"], supports_count=True,
                         is_hidden=True)
        self.add_command("scroll_lib", self._app["library"].scroll,
                         positional_args=["direction"], supports_count=True,
                         is_hidden=True)
        self.add_command("search", self._app["commandline"].enter_search,
                         is_hidden=True)
        self.add_command("search_next",
                         self._app["commandline"].search_move,
                         default_args=[True], supports_count=True,
                         is_hidden=True)
        self.add_command("search_prev",
                         self._app["commandline"].search_move,
                         default_args=[False], supports_count=True,
                         is_hidden=True)
        self.add_command("slider", self._app["manipulate"].change_slider,
                         optional_args=["value"], supports_count=True,
                         is_hidden=True)
        # Aliases
        aliases = settings.get_aliases()
        message = ""
        for alias in aliases:
            try:
                self._add_alias(alias, aliases[alias])
            except AliasError as e:
                message += str(e) + "\n"
        if message:
            error_message(message, running_tests=self._app.running_tests)
        aliases.clear()

    def set(self, setting, value=None):
        """Wrapper for settings.override catching errors."""
        # Allow passing multipliers via keybinding
        multiplier = self._app["eventhandler"].get_num_str()
        if multiplier:
            self._app["eventhandler"].num_clear()
        else:
            multiplier = "1"
        try:
            # Toggle boolean settings
            if setting.endswith("!"):
                setting = setting.rstrip("!")
                settings.toggle(setting)
            # Add to number settings
            elif value and value.startswith("+") or value.startswith("-"):
                settings.add_to(setting, value, multiplier)
            else:
                settings.override(setting, value)
        except (StringConversionError, SettingNotFoundError, NotABoolean,
                NotANumber) as e:
            self._app["statusbar"].message(str(e), "error")

    def __getitem__(self, name):
        """Return the command corresponding to name.

        Args:
            name: The name of the command to access.
        Return:
            Dictionary of the command information.
        """
        return self._commands[name]

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        """Iterate over commands."""
        items = list(self._commands.values())
        if (self._n - 1) < len(items) - 1:
            self._n += 1
            return items[self._n - 1]
        else:
            raise StopIteration

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
        command = Command(name, function)
        command.set_default_args(default_args)
        command.set_positional_args(positional_args)
        command.set_optional_args(optional_args)
        command.set_supports_count(supports_count)
        command.set_is_hidden(is_hidden)
        self._commands[name] = command

    def add_alias(self, name, command_name):
        """Wrapper for self._add_alias which displays error messages.

        Args:
            name: Name of the alias.
            command_name: Name of the original command.
        """
        try:
            self._add_alias(name, command_name)
        except AliasError as e:
            self._app["statusbar"].message(str(e), "error")

    def _add_alias(self, name, command_name):
        """Add an alias.

        Args:
            name: Name of the alias.
            command_name: Name of the original command.
        """
        command = command_name.split()[0]
        if name in self._commands.keys():
            raise AliasError('Alias "%s" would overwrite an existing command'
                             % (name))
        if command not in self._commands.keys() \
                and command_name[0] not in "!~/.":
            raise AliasError('Alias "%s" failed: no command called "%s"'
                             % (name, command_name))
        self.aliases[name] = command_name


class Command(object):
    """Stores a single command and its attributes.

    Attributes:
        name: Name of the command as used in the command line.
        function: Function the command should call.
        default_args: Default arguments to pass to the function.
        positional_args: Arguments that must be passed by the user.
        optional_args: Arguments that may be passed by the user.
        supports_count: If false, delete any num_str before running the
            command.
        is_hidden: If true, hide command from the command line.
    """

    def __init__(self, name, function):
        """Generate command and set all attributes.

        Args:
            name: Name of the command as used in the command line.
            function: Function the command should call.
        """
        self.name = name
        self.function = function
        self.default_args = None
        self.positional_args = None
        self.optional_args = None
        self.supports_count = False
        self.is_hidden = False

    def set_default_args(self, args):
        self.default_args = args

    def set_positional_args(self, args):
        self.positional_args = args

    def set_optional_args(self, args):
        self.optional_args = args

    def set_supports_count(self, supports_count):
        self.supports_count = supports_count

    def set_is_hidden(self, is_hidden):
        self.is_hidden = is_hidden

    def get_max_args(self):
        """Return the maximum amount of arguments a command may receive.

        Return:
            The maximum of arguments as integer.
        """
        num = 0
        if self.positional_args:
            num += len(self.positional_args)
        if self.optional_args:
            num += len(self.optional_args)
        return num

    def get_min_args(self):
        return len(self.positional_args) if self.positional_args else 0
