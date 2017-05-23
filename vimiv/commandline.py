# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains the commandline class for vimiv."""

import os
import re
from bisect import bisect_left, bisect_right
from subprocess import PIPE, Popen
from threading import Thread

from gi.repository import GLib, Gtk
from vimiv.helpers import read_file, error_message, expand_filenames


class CommandLine(Gtk.Entry):
    """Commandline of vimiv.

    Attributes:
        search_positions: Search results as positions.
        running_processes: List of all running external processes.

        _app: The main vimiv application to interact with.
        _history: List of commandline history to save.
        _incsearch: If True, enable incremental search in the library.
        _last_focused: Widget that was focused before the command line.
        _last_index: Index that was last selected in the library, if any.
        _matching_history: Parts of the history that match entered text.
        _pos: Position in history completion.
        _search_case: If True, search case sensitively.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(CommandLine, self).__init__()
        self._app = app
        general = settings["GENERAL"]

        # Command line
        self.connect("activate", self._on_activate)
        self.connect("key_press_event",
                     self._app["eventhandler"].on_key_press, "COMMAND")
        self.connect("changed", self._on_text_changed)
        self.set_hexpand(True)

        # Cmd history from file
        datadir = os.path.join(GLib.get_user_data_dir(), "vimiv")
        os.makedirs(datadir, exist_ok=True)
        # If there is a history file in the old location move it and inform the
        # user
        # TODO remove this in a new version, assigned for 0.10
        old_histfile = os.path.expanduser("~/.vimiv/history")
        new_histfile = os.path.join(datadir, "history")
        if os.path.isfile(old_histfile):
            if os.path.isfile(new_histfile):
                message = "There is a history file in the deprecated location" \
                    " %s and the new location %s. Using the new one. If you " \
                    "want the history from the old file you will have to " \
                    "merge it manually." % (old_histfile, new_histfile)
                error_message(message, running_tests=self._app.running_tests)
            else:
                os.rename(old_histfile, new_histfile)
                message = "Moved the old history file %s " \
                    "to the new location %s." % (old_histfile, new_histfile)
                error_message(message, running_tests=self._app.running_tests)
        self._history = read_file(os.path.join(datadir, "history"))

        # Defaults
        self._pos = 0
        self._matching_history = []
        self.search_positions = []
        self._search_case = general["search_case_sensitive"]
        self._incsearch = general["incsearch"]
        if self._incsearch:
            self.connect("changed", self._do_incsearch)
        self._last_index = 0
        self.running_processes = []
        self._last_focused = ""

    def _on_activate(self, entry):
        """Handle input from the entry when activated.

        Check for type of command (internal, external, path or alias) and run
        the correct function.

        Args:
            entry: The Gtk.Entry from which the command comes.
        """
        # Only close completions if currently tabbing through results
        if self._app["completions"].activate_tab_completion():
            return
        # cmd from input
        command = entry.get_text()
        # Check for alias and update command
        if command[1:] in self._app.aliases:
            command = ":" + self._app.aliases[command[1:]]
        # And close the cmd line by emptying text
        self.set_text("")
        # Write command to log in debug mode
        if self._app.debug:
            self._app["log"].write_message("commandline", command)
        # Save the cmd to the history list avoiding duplicates
        if command in self._history:
            self._history.remove(command)
        self._history.insert(0, command)
        # Reset history position
        self._pos = 0
        # Run the correct command
        self._run(command)

    def _run(self, command):
        """Run correct function for command.

        Calls one of search, run_external_command, run_path and run_command.

        Args:
            command: The command to operate on.
        """
        if command[0] == "/":  # Search
            # Do not search again if incsearch was running
            if not (self._app["library"].is_focus() or
                    self._app["thumbnail"].is_focus()) or \
                    not self._incsearch:
                self._run_search(command.lstrip("/"))
            # Auto select single file in the library
            elif self._incsearch and len(self.search_positions) == 1 and \
                    self._app["library"].is_focus():
                self._app["library"].file_select(
                    self._app["library"],
                    Gtk.TreePath(self._app.get_pos()), None, False)
        else:  # Run a command
            cmd = command.lstrip(":")
            # If there was no command just leave
            if not cmd:
                return
            # Run something different depending on first char in cmd
            if cmd[0] == "!":
                self._run_external_command(cmd[1:])  # Strip the !
            elif cmd[0] == "~" or cmd[0] == "." or cmd[0] == "/":
                self._run_path(cmd)
            else:  # Default to internal cmd
                self._app["eventhandler"].num_clear()
                while cmd[0].isdigit():
                    self._app["eventhandler"].num_str += cmd[0]
                    cmd = cmd[1:]
                self.run_command(cmd)

    # Public because keyhandler also calls this
    def run_command(self, cmd, keyname=None):
        """Run the correct internal command.

        Args:
            cmd: Internal command to run.
            keyname: Key that called run_command. Passed when called from
                eventhandler.
        """
        # Get name and arguments
        name_func_and_args = cmd.split()
        if cmd.startswith("set "):
            name_func = " ".join(name_func_and_args[0:2])
            conf_args = name_func_and_args[2:]
        else:
            name_func = name_func_and_args[0]
            conf_args = name_func_and_args[1:]
        if name_func in self._app["commands"]:
            cmd_dict = self._app["commands"][name_func]
            # Do not allow calling hidden commands from the command line
            if not keyname and cmd_dict["is_hidden"]:
                message = "Called a hidden command from the command line"
                self._app["statusbar"].message(message, "error")
                return
            # Check if the amount of arguments
            if len(conf_args) < len(cmd_dict["positional_args"]):
                message = "Missing positional arguments for command " + \
                    name_func + ": " + ", ".join(cmd_dict["positional_args"])
                self._app["statusbar"].message(message, "error")
            elif len(conf_args) > len(cmd_dict["positional_args"]) + \
                    len(cmd_dict["optional_args"]):
                message = "Too many arguments for command " + name_func
                self._app["statusbar"].message(message, "error")
            else:
                # Check if the function supports passing count
                if not cmd_dict["supports_count"]:
                    self._app["eventhandler"].num_clear()
                args = cmd_dict["default_args"] + conf_args
                cmd_dict["function"](*args)
        # If the command name is not in the dictionary throw an error
        else:
            message = "No command called " + name_func
            if keyname:
                message += " bound to " + keyname
            self._app["statusbar"].message(message, "error")

    def _run_external_command(self, cmd):
        """Run the entered command in the terminal.

        Args:
            cmd: The command to run.
        """
        # Expand filenames getting the correct filelist to operate on first
        fil = self._app.get_pos(True)
        if self._app["mark"].marked:  # Always use marked files if they exist
            filelist = list(self._app["mark"].marked)
        elif self._last_focused == "lib":
            filelist = list(self._app["library"].files)
        elif self._last_focused in ["thu", "im"]:
            filelist = list(self._app.get_paths())
        else:  # Empty filelist as a fallback
            filelist = []
        # Only do substitution if a filelist exists
        if filelist:
            cmd = expand_filenames(fil, filelist, cmd)
        # Possibility to "pipe to vimiv"
        if cmd[-1] == "|":
            cmd = cmd.rstrip("|")
            p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            from_pipe = True
        else:
            p = Popen(cmd, stderr=PIPE, shell=True)
            from_pipe = False
        self.running_processes.append(p)
        # Run the command in an extra thread, useful e.g. for gimp %
        cmd_thread = Thread(target=self._thread_for_external,
                            args=(cmd, p, from_pipe))
        cmd_thread.start()

    def _thread_for_external(self, cmd, p, from_pipe):
        """Start a new thread for external commands.

        Args:
            cmd: The command to run.
            directory: Directory which is affected by command.
        """
        # Get output and error and run the command
        out, err = p.communicate()
        if p.returncode:
            message = "Command exited with status " + str(p.returncode) + "\n"
            message += err.decode()
            GLib.idle_add(self._app["statusbar"].message, message, "error")
        else:
            # Run pipe if we have output
            if from_pipe and out:
                GLib.idle_add(self._run_pipe, out)
            # We do not know what might have changed concerning paths
            else:
                GLib.idle_add(self._app.emit, "paths-changed", self)
        self.running_processes.pop()

    def _run_pipe(self, pipe_input):
        """Run output of external command in a pipe.

        This checks for directories, files and vimiv commands.

        Args:
            pipe_input: Command that comes from pipe.
        """
        # Leave if no pipe_input came
        if not pipe_input:
            self._app["statusbar"].message("No input from pipe", "info")
            return
        # Make the pipe_input a file
        pipe_input = pipe_input.decode("utf-8")
        # List of commands without empty line
        pipe_input = pipe_input.split("\n")[:-1]
        startout = pipe_input[0]
        # Do different stuff depending on the first line of pipe_input
        if os.path.isdir(startout):
            self._app["library"].move_up(startout)
        elif os.path.isfile(startout):
            # Remember old file if no image was in filelist
            if self._app.get_paths():
                old_pos = self._app.get_index()
            else:
                old_pos = []
            # Populate filelist
            self._app.populate(pipe_input)
            if self._app.get_paths():  # Images were found
                self._app["main_window"].show()
                self._app["image"].load()
                # Resize library and focus image if necessary
                if self._app["library"].grid.is_visible():
                    self._app["library"].set_hexpand(False)
                    self._app["library"].focus(False)
            elif old_pos:  # Nothing found, go back
                self._app.populate(old_pos)
                self._app["statusbar"].message("No image found", "info")
        else:  # Run every line as an internal command
            for cmd in pipe_input:
                self.run_command(cmd)

    def _run_path(self, path):
        """Run a path command, namely populate files or focus directory.

        Args:
            path: The path to run on.
        """
        # Expand home and use absolute path
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.exists(path):
            if os.path.isdir(path):
                # Focus directory in the library
                self._app["library"].move_up(path)
                self._last_focused = "lib"
            else:
                # If it is an image open it
                self._app.populate([path])
                self._app["image"].load()
                #  Reload library in lib mode, do not open it in image mode
                pathdir = os.path.dirname(path)
                if self._last_focused == "lib":
                    self._app["library"].move_up(pathdir)
                    # Focus it in the treeview so it can be accessed via "l"
                    index = \
                        self._app["library"].files.index(os.path.basename(path))
                    self._app["library"].set_cursor(
                        Gtk.TreePath(index), None, False)
                    # Show the image
                    self._app["library"].set_hexpand(False)
                    self._app["main_window"].show()
                else:
                    self._app["library"].move_up(pathdir, True)
        else:
            self._app["statusbar"].message("Not a valid path", "error")

    def history_search(self, down):
        """Search through history with substring match.

        Updates the text of self with the matching history search.

        Args:
            down: If True, search downwards. Else search upwards.
        """
        # Shortly disconnect the change signal as it resets the history search
        self.disconnect_by_func(self._on_text_changed)
        # Only parts of the history that match the entered text
        if not self._matching_history:
            substring = self.get_text()
            matchstr = "^(" + substring + ")"
            self._matching_history = [substring]
            for cmd in self._history:
                if re.match(matchstr, cmd):
                    self._matching_history.append(cmd)
        # Move and set the text
        if down:
            self._pos -= 1
        else:
            self._pos += 1
        self._pos = self._pos % len(self._matching_history)
        self.set_text(self._matching_history[self._pos])
        self.set_position(-1)
        # Reconnect when done
        self.connect("changed", self._on_text_changed)

    def focus(self, text=""):
        """Open and focus the command line."""
        # Colon for text
        self.set_text(":" + text)
        # Show/hide the relevant stuff
        self.show()
        self._app["completions"].show()
        # Remember what widget was focused before
        self._last_focused = self._app.get_focused_widget()
        self.reset_search(leaving=False)
        self.grab_focus()
        self.set_position(-1)
        # Update info for command mode
        self._app["statusbar"].update_info()

    def _on_text_changed(self, entry):
        """Close the entry if the colon/slash is deleted and reset search.

        Args:
            entry: The Gtk.Entry to check.
        """
        self._matching_history = []
        self._pos = 0
        text = entry.get_text()
        if not text or text[0] not in ":/":
            self.leave()

    def leave(self, reset_search=False):
        """Apply actions to close the commandline."""
        self._app["completions"].scroll_to_point(0, 0)
        self.hide()
        self._app["completions"].hide()
        self._app["completions"].reset()
        # Refocus the remembered widget
        if self._last_focused == "lib":
            self._app["library"].focus(True)
        elif self._last_focused == "man":
            self._app["manipulate"].sliders["bri"].grab_focus()
        elif self._last_focused == "thu":
            self._app["thumbnail"].grab_focus()
        else:
            self._app["main_window"].grab_focus()
        if reset_search:
            self.reset_search(leaving=True)
        self._last_index = 0
        self._app["statusbar"].update_info()

    def _do_incsearch(self, entry):
        """Run a search for every entered character.

        Args:
            entry: The Gtk.Entry to check.
        """
        text = entry.get_text()
        if (not self._last_focused == "lib"
                and not self._last_focused == "thu") \
                or len(text) < 2:
            return
        elif text[0] == "/":
            self._run_search(text.lstrip("/"), True)

    def cmd_search(self):
        """Prepend search character '/' to the cmd_line and open it."""
        self.focus()
        self.set_text("/")
        self.set_position(-1)

    def _run_search(self, searchstr, incsearch=False):
        """Run a search on the appropriate filelist.

        Args:
            searchstr: The search string to parse.
            incsearch: Do incremental search or not.
        """
        if self._last_focused == "lib":
            paths = self._app["library"].files
        else:
            paths = [os.path.basename(path) for path in self._app.get_paths()]

        # Fill search_positions with matching files depending on search_case
        self.search_positions = \
            [paths.index(fil) for fil in paths
             if searchstr in fil
             or not self._search_case and searchstr.lower() in fil.lower()]

        # Reload library and thumbnails to show search results
        if self._last_focused == "lib":
            self._app["library"].focus(True)
            self._app["library"].reload_names()
        elif self._last_focused == "thu":
            # Reload all thumbnails in incsearch, only some otherwise
            if incsearch:
                self._app["thumbnail"].grab_focus()
                for image in self._app.get_paths():
                    self._app["thumbnail"].reload(image, False)
            else:
                for index in self.search_positions:
                    self._app["thumbnail"].reload(self._app.get_paths()[index],
                                                  False)

        # Move to first result or throw an error
        if self.search_positions:
            self._search_move_internal(incsearch)
        elif incsearch:
            self.grab_focus()
            self.set_position(-1)
        else:
            self._app["statusbar"].message("No matching file", "info")

    def search_move(self, forward=True):
        """Move to the next or previous search.

        Args:
            forward: If true, move forwards. Else move backwards.
        """
        if not self.search_positions:
            self._app["statusbar"].message("No search results", "warning")
            return
        # Correct handling of prefixed numbers
        add_on = self._app["eventhandler"].num_receive() - 1
        # Next position depending on current position and direction
        pos = self._app.get_pos()
        if forward:
            index = bisect_right(self.search_positions, pos) + add_on
        else:
            index = bisect_left(self.search_positions, pos) - 1 - add_on
        next_pos = self.search_positions[index % len(self.search_positions)]
        self._file_select(next_pos, incsearch=False)

    def _search_move_internal(self, incsearch=False):
        """Select the first search match when called from search internally.

        Args:
            incsearch: Do incremental search or not.
        """
        pos = self._app.get_pos()
        index = bisect_left(self.search_positions, pos)
        next_pos = self.search_positions[index % len(self.search_positions)]
        self._file_select(next_pos, incsearch)

    def _file_select(self, position, incsearch):
        """Select next file from search in library, image or thumbnail.

        Args:
            position: Position of the file to select.
            incsearch: Do incremental search or not.
        """
        # Select new file in library, image or thumbnail
        if self._last_focused == "lib":
            self._app["library"].set_cursor(Gtk.TreePath(position), None, False)
            self._app["library"].scroll_to_cell(Gtk.TreePath(position),
                                                None, True, 0.5, 0)
            # Auto select single file
            if len(self.search_positions) == 1 and not self._incsearch:
                self._app["library"].file_select(
                    self._app["library"], Gtk.TreePath(position), None,
                    False)
        elif self._last_focused == "im":
            self._app["eventhandler"].num_str = str(position + 1)
            self._app["image"].move_pos()
        elif self._last_focused == "thu":
            self._app["thumbnail"].move_to_pos(position)
        # Refocus entry if incsearch is appropriate
        if incsearch and not self._last_focused == "im":
            self.grab_focus()
            self.set_position(-1)

    def reset_search(self, leaving):
        """Reset all search parameters to null.

        Args:
            leaving: If True, leaving the commandline. Else entering.
        """
        self.search_positions = []
        # Remember position when entering
        if not leaving:
            self._last_index = self._app.get_pos()
        # Reload library or thumbnail
        if self._last_focused == "lib":
            self._app["library"].reload_names()
            if leaving:
                self._app["library"].set_cursor(
                    Gtk.TreePath(self._last_index), None, False)
                self._app["library"].scroll_to_cell(
                    Gtk.TreePath(self._last_index), None, True, 0.5, 0)
        elif self._last_focused == "thu":
            for image in self._app.get_paths():
                self._app["thumbnail"].reload(image, False)
            if leaving:
                self._app["thumbnail"].move_to_pos(self._last_index)

    def add_alias(self, alias, *command):
        """Add an alias.

        Args:
            alias: The alias to set up.
            command: Command to be called.
        """
        self._app.aliases[alias] = " ".join(command)

    def get_history(self):
        return self._history

    def write_history(self):
        """Write commandline history to file."""
        histfile = os.path.join(GLib.get_user_data_dir(), "vimiv", "history")
        with open(histfile, "w") as f:
            for cmd in self._history:
                f.write(cmd + "\n")

    def toggle_search_case(self):
        self._search_case = not self._search_case
