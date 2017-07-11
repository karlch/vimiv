# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""The commandline completion for vimiv."""

import os
import re
from itertools import takewhile
from string import digits

from gi.repository import GLib, Gtk
from vimiv.fileactions import is_image
from vimiv.helpers import listdir_wrapper, read_info_from_man
from vimiv.settings import settings


class Completion(Gtk.TreeView):
    """Completion for vimiv's commandline.

    Attributes:
        info: ScrolledWindow containing the completion information.

        _app: The main vimiv application to interact with.
        _liststores: Dictionary containing the liststore models for different
            completion types.
        _prefixed_digits: User prefixed digits for internal command.
        _tab_position: Position when tabbing through completion elements.
        _tab_presses: Amount of tab presses.
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        super(Completion, self).__init__()
        self._app = app
        # Create liststore dictionary with the filter used.
        self._liststores = {"internal": [Gtk.ListStore(str, str)],
                            "external": [Gtk.ListStore(str, str)],
                            "path": [Gtk.ListStore(str, str)],
                            "tag": [Gtk.ListStore(str, str)],
                            "search": [Gtk.ListStore(str, str)],
                            "trash": [Gtk.ListStore(str, str)],
                            "setting": [Gtk.ListStore(str, str)]}
        for liststore in self._liststores.values():
            comp_filter = liststore[0].filter_new()
            comp_filter.set_visible_func(self._completion_filter)
            liststore.append(comp_filter)
        # Use the commandline entry here and connect to the refilter method
        self._app["commandline"].connect("changed", self._refilter)
        # Edit treeview
        self.set_enable_search(False)
        self.set_headers_visible(False)
        self.set_activate_on_single_click(True)
        padding = settings["commandline_padding"].get_value()
        renderer = Gtk.CellRendererText()
        renderer.set_padding(padding, 0)
        command_column = Gtk.TreeViewColumn("Command", renderer, markup=0)
        command_column.set_expand(True)
        self.append_column(command_column)
        info_column = Gtk.TreeViewColumn("Info", renderer, markup=1)
        self.append_column(info_column)
        self.connect("row-activated", self._activate)
        # Scrolled window for the completion info
        self.info = Gtk.ScrolledWindow()
        self.info.set_size_request(
            10, settings["completion_height"].get_value())
        self.info.add(self)
        # Defaults
        self._tab_position = 0
        self._tab_presses = 0
        self._prefixed_digits = ""

    def generate_commandlist(self):
        """Generate a list of internal vimiv commands and store it."""
        commands = [cmd.name for cmd in self._app["commandline"].commands
                    if not cmd.is_hidden]
        aliases = list(self._app["commandline"].commands.aliases.keys())
        all_commands = sorted(commands + aliases)
        infodict = read_info_from_man()
        for command in all_commands:
            if command in infodict:
                info = infodict[command]
            elif command in aliases:
                info = "Alias to %s" % (
                    self._app["commandline"].commands.aliases[command])
            else:
                info = ""
            info = "<i>" + GLib.markup_escape_text(info) + "</i>"
            self._liststores["internal"][0].append([command, info])

    def show(self):
        """Show the completion information."""
        # Hacky way to not show the last selected item
        self.set_model(Gtk.ListStore(str, str))
        self._refilter(self._app["commandline"])
        self.info.show()

    def hide(self):
        """Hide the completion information."""
        self.info.hide()

    def activate_tab_completion(self):
        """Select tab completion when commandline was activated.

        Return:
            Boolean: True if completion was selected, False else.
        """
        if self._tab_presses:
            self._activate(None, None, None)
            self.reset()
            return True
        return False

    def _activate(self, treeview, path, column):
        """Enter the completion text of the treeview into the commandline.

        Args:
            treeview: TreeView that was activated.
            path: Activated TreePath.
            column: Activated TreeViewColumn.
        """
        if treeview:
            count = path.get_indices()[0]
            self._app["commandline"].grab_focus()
        else:
            count = self._tab_position
        comp_type = self._get_comp_type()
        row = self._liststores[comp_type][1][count]
        self._app["commandline"].set_text(":" + self._prefixed_digits + row[0])
        self._app["commandline"].set_position(-1)

    def reset(self):
        """Reset all internal counts."""
        self._tab_position = 0
        self._tab_presses = 0

    def complete(self, inverse=False):
        """Run completion.

        Try to enter the best matching completion into the entry. On more than
        one tab start to run through the possible completions.

        Args:
            inverse: If True, tabbing backwards.
        """
        maximum = len(self.get_model())
        # If we have no entries, completing makes no sense
        if not maximum:
            return
        # Try to set best match first
        elif not self._tab_presses:
            best_match = ":" + self._prefixed_digits
            comp_type = self._get_comp_type()
            liststore = self._liststores[comp_type][1]
            first = str(liststore[0][0])
            last = str(liststore[-1][0])
            for i, char in enumerate(first):
                if char == last[i]:
                    best_match += char
                else:
                    break
            if best_match != self._app["commandline"].get_text():
                self._app["commandline"].set_text(best_match)
                self._app["commandline"].set_position(-1)
                return
            # Start at the last element with Shift+Tab
            elif inverse:
                self._tab_position = -1
        # Set position according to direction and move
        elif inverse:
            self._tab_position -= 1
        else:
            self._tab_position += 1
        self._tab_presses += 1
        self._tab_position %= maximum
        self.set_cursor(Gtk.TreePath(self._tab_position), None, False)
        self.scroll_to_cell(Gtk.TreePath(self._tab_position),
                            None, True, 0.5, 0)
        return True  # Deactivate default keybinding (here for Tab)

    def _get_comp_type(self, command=""):
        """Get the current completion type depending on command.

        Args:
            command: The command to check completion type for. If there is none,
                default to getting the text from self._app["commandline"].
        Return:
            The completion type to use.
        """
        if not command:
            command = self._app["commandline"].get_text()
        if command and command[0] != ":":
            return "search"
        command = command.lstrip(":")
        # Nothing entered -> checks are useless
        if command:
            # External commands are prefixed with an !
            if command[0] == "!":
                return "external"
            # Paths are prefixed with a /
            elif command[0] in ["/", ".", "~"]:
                return "path"
            # Tag commands
            elif re.match(r'^(tag_(write|remove|load) )', command):
                return "tag"
            # Undelete files from trash
            elif command.startswith("undelete"):
                return "trash"
            # Settings
            elif command.startswith("set"):
                return "setting"
        return "internal"

    def _complete_path(self, path):
        """Complete paths.

        Args:
            path: (Partial) name of the path to run completion on.
        Return:
            List containing formatted matching paths.
        """
        self._liststores["path"][0].clear()
        # Directory of the path, default to .
        directory = os.path.dirname(path) if os.path.dirname(path) else path
        if not os.path.exists(os.path.expanduser(directory)) \
                or not os.path.isdir(os.path.expanduser(directory)):
            directory = "."
        # /dev causes havoc
        if directory == "/dev":
            return
        # Files in that directory
        files = listdir_wrapper(directory, settings["show_hidden"].get_value())
        # Format them neatly depending on directory and type
        for fil in files:
            fil = os.path.join(directory, fil)
            # Directory
            if os.path.isdir(os.path.expanduser(fil)):
                self._liststores["path"][0].append([fil + "/", ""])
            # Acceptable file
            elif is_image(fil):
                self._liststores["path"][0].append([fil, ""])

    def _complete_tag(self, command):
        """Append the available tag names to an internal tag command.

        Args:
            command: The internal command to complete.
        """
        self._liststores["tag"][0].clear()
        tags = listdir_wrapper(self._app["tags"].directory,
                               settings["show_hidden"].get_value())
        for tag in tags:
            self._liststores["tag"][0].append([command.split()[0] + " " + tag,
                                               ""])

    #  The function currently only hides the commandline but is implemented
    #  for possible future usage.
    def _complete_search(self):
        """Hide the info as it has no use in search."""
        self.info.hide()

    def _complete_external(self, command):
        """If there is more than one word in command, do path completion.

        Args:
            command: The external command to complete.
        """
        self._liststores["external"][0].clear()
        command = command.lstrip("!").lstrip(" ")
        spaces = command.count(" ")
        # If there are spaces, path completion for external commands makes sense
        if spaces:
            args = command.split()
            # Last argument is the path to complete
            if len(args) > spaces:
                path = args[-1]
                # Do not try path completion for arguments
                if path.startswith("-"):
                    self.info.hide()
                    return
                command = " ".join(args[:-1]) + " "
            else:
                path = "./"
            self._complete_path(path)
            # Prepend command to path completion
            # Gtk ListStores are iterable
            # pylint:disable=not-an-iterable
            for row in self._liststores["path"][0]:
                match = "!" + command + re.sub(r'^\./', "", row[0])
                self._liststores["external"][0].append([match, ""])
        else:
            self.info.hide()

    def _complete_trash(self, command):
        """Complete files in trash directory for :undelete.

        Args:
            command: The internal command to complete.
        """
        # Get files in trash directory
        self._liststores["trash"][0].clear()
        trash_directory = \
            self._app["transform"].trash_manager.get_files_directory()
        trash_files = sorted(os.listdir(trash_directory))
        # Add them to completion formatted to 'undelete $FILE'
        for fil in trash_files:
            # Ensure we only complete image files as vimiv is not meant as a
            # general trash tool but provides this for convenience
            abspath = os.path.join(trash_directory, fil)
            if is_image(abspath):
                completion = "undelete %s" % (fil)
                self._liststores["trash"][0].append([completion, ""])

    def _complete_setting(self, command):
        """Complete settings for :set.

        Args:
            command: The internal command to complete.
        """
        self._liststores["setting"][0].clear()
        # Get all settings
        setting_names = [setting.name for setting in settings]
        # Add them to completion formatted to 'set $SETTING'
        for name in setting_names:
            completion = "set %s" % (name)
            typestr = str(type(settings[name].get_value()))
            typestr = typestr.replace("<class '", "").rstrip("'>")
            info = "<i>" + typestr + "</i>"
            self._liststores["setting"][0].append([completion, info])

    def _completion_filter(self, model, treeiter, data):
        """Filter function used in the liststores to filter completions.

        Args:
            model: The liststore model to filter.
            treeiter: The TreeIter representing a row in the model.
            data: User appended data, here the completion mode.
        Return:
            True for a match, False else.
        """
        command = self._app["commandline"].get_text().lstrip(":")
        # Allow number prefixes
        self._prefixed_digits = "".join(takewhile(str.isdigit, command))
        command = command.lstrip(digits)
        return model[treeiter][0].startswith(command)

    def _refilter(self, entry):
        """Refilter the completion list according to the text in entry."""
        # Replace multiple spaces with single space
        entry.set_text(re.sub(r' +', " ", entry.get_text()))
        comp_type = self._get_comp_type()
        command = entry.get_text().lstrip(":")
        if command:
            self.info.show()
        if comp_type == "path":
            self._complete_path(command)
        elif comp_type == "tag":
            self._complete_tag(command)
        elif comp_type == "search":
            self._complete_search()
        elif comp_type == "external":
            self._complete_external(command)
        elif comp_type == "trash":
            self._complete_trash(command)
        elif comp_type == "setting":
            self._complete_setting(command)
        self.set_model(self._liststores[comp_type][1])
        self._liststores[comp_type][1].refilter()
        self.reset()
