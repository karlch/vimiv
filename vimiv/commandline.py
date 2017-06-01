# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains the commandline class for vimiv."""

import os
import re
from subprocess import PIPE, Popen
from threading import Thread

from gi.repository import GLib, Gtk, GObject
from vimiv.helpers import read_file, error_message, expand_filenames


class CommandLine(Gtk.Entry):
    """Commandline of vimiv.

    Attributes:
        search: Search class defined below.
        running_processes: List of all running external processes.

        _app: The main vimiv application to interact with.
        _history: List of commandline history to save.
        _last_widget: Widget that was focused before the command line.
        _last_index: Index that was last selected in the library, if any.
        _matching_history: Parts of the history that match entered text.
        _pos: Index in _history list.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        super(CommandLine, self).__init__()
        self._app = app

        # Command line
        self.connect("activate", self._on_activate)
        self.connect("key_press_event",
                     self._app["eventhandler"].on_key_press, "COMMAND")
        self.connect("changed", self._on_text_changed)
        self.set_hexpand(True)

        # Initialize search
        self.search = Search(self, settings)

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
        self._matching_history = []
        self._last_index = 0
        self._pos = 0
        self.running_processes = []
        self._last_widget = ""

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
            self.search.run(command[1:])  # Strip /
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
        elif self._last_widget == "lib":
            filelist = list(self._app["library"].files)
        elif self._last_widget in ["thu", "im"]:
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
            if from_pipe:
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
        # List of commands without empty line
        pipe_input = pipe_input.decode("utf-8")
        pipe_input = pipe_input.split("\n")[:-1]
        startout = pipe_input[0] if pipe_input else ""
        # Leave if no pipe_input came
        if not startout or startout.isspace():
            self._app["statusbar"].message("No input from pipe", "info")
            return
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
            else:
                if old_pos:  # Back again if there is a remembered image
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
                self._last_widget = "lib"
            else:
                # If it is an image open it
                self._app.populate([path])
                self._app["image"].load()
                #  Reload library in lib mode, do not open it in image mode
                pathdir = os.path.dirname(path)
                if self._last_widget == "lib":
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

    def enter(self, text=""):
        """Prepend ':' to the cmd_line and open it.

        Args:
            text: Additionally add this to the command line.
        """
        self.set_text(":" + text)
        self._focus()

    def enter_search(self):
        """Prepend search character '/' to the cmd_line and open it."""
        focused_file = self._app.get_pos(True)
        self.set_text("/")
        self._focus()
        self.set_position(-1)
        if self._last_widget == "lib":
            paths = self._app["library"].files
        else:
            paths = [os.path.basename(path) for path in self._app.get_paths()]
        self.search.init(paths, focused_file, self._last_widget)

    def _focus(self):
        """Open and focus the command line."""
        # Show/hide the relevant stuff
        self.show()
        self._app["completions"].show()
        # Remember what widget was focused before
        self._last_widget = self._app.get_focused_widget()
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
        if self._last_widget == "lib":
            self._app["library"].focus(True)
        elif self._last_widget == "man":
            self._app["manipulate"].sliders["bri"].grab_focus()
        elif self._last_widget == "thu":
            self._app["thumbnail"].grab_focus()
        else:
            self._app["main_window"].grab_focus()
        if reset_search:
            self.search.reset()
        self._last_index = 0
        self._app["statusbar"].update_info()

    def search_move(self, forward=True):
        """Move to the next or previous search.

        Args:
            forward: If true, move forwards. Else move backwards.
        """
        repeat = self._app["eventhandler"].num_receive()
        focused_file = os.path.basename(self._app.get_pos(True))
        if self.search.next_result(forward, repeat, focused_file):
            self._app["statusbar"].message("No search results to navigate",
                                           "error")

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


class Search(GObject.Object):
    """Handle search for vimiv.

    Filelist gets set upon commandline entry. When search through filelist was
    completed, the "search-completed" signal gets emitted.

    Attributes:
        results: List of files in search results.

        _incsearch: If True, enable incremental search.
        _filelist: List of files to operate search on.
        _last_file: Filename that was focused before search.
        _last_widget: Widget that was focused before search.
        _search_case: If True, search case sensitively.

    Signals:
        search-completed: Emitted when a search was completed so the widgets can
            react accordingly (focus new path, show search results, ...).
        no-search-results: Emitted when a search was result-less to show a
            warning.
    """

    def __init__(self, commandline, settings):
        """Create necessary objects and settings.

        Args:
            commandline: Commandline to interact with.
            settings: Settings from configfiles to use.
        """
        super(Search, self).__init__()

        self._filelist = []
        self._last_file = ""
        self.results = []
        general = settings["GENERAL"]
        self._incsearch = general["incsearch"]
        self._search_case = general["search_case_sensitive"]
        self._last_widget = ""

        if self._incsearch:
            commandline.connect("changed", self._do_incsearch)

    def _do_incsearch(self, entry):
        """Run a search for every entered character.

        Args:
            entry: The Gtk.Entry to check.
        """
        text = entry.get_text()
        if text[1:] and text[0] == "/" and self._last_widget != "im":
            self.run(text[1:])

    def init(self, filelist, focused_file, last_focused):
        """Initialize values needed for search.

        Called when entering the command line.
        """
        self._filelist = filelist
        self._last_file = os.path.basename(focused_file)
        self._last_widget = last_focused
        self.reset()

    def run(self, searchstr):
        """Start a search through filelist and emit search-completed signal."""
        self.results = \
            [fil for fil in self._filelist
             if searchstr in fil
             or not self._search_case and searchstr.lower() in fil.lower()]
        if self.results:
            self.next_result(forward=True)
        else:
            self.emit("no-search-results", searchstr)

    def next_result(self, forward=True, repeat=1, focused_file=""):
        """Move to next search result by emitting search-completed.

        Args:
            forward: If True, search forward in list. Else backwards.
            repeat: Steps coming from eventhandler.
            focused_file: File that is focused before calling this. Required as
                this may be called with keybindings.
        Return: 1 if failed, 0 if successfull
        """
        if focused_file:
            self._last_file = focused_file
        count = 0
        # Order filelist according to last position
        filelist = list(self._filelist)
        if not forward:
            filelist.reverse()
        try:
            index = filelist.index(self._last_file) + 1
        # Search move called in a directory without search
        except ValueError:
            return 1
        filelist = filelist[index:] + filelist[:index]
        # Find next match
        for i, f in enumerate(filelist):
            if f in self.results:
                count += 1
                if repeat == count:
                    new_pos = (index + i) if forward \
                        else len(self._filelist) - 1 - (index + i)
                    new_pos %= len(self._filelist)
                    self.emit("search-completed", new_pos, self._last_widget)
                    break
        return 0

    def reset(self):
        """Reset search and trigger reload of widgets."""
        last_pos = self._filelist.index(self._last_file) \
            if self._last_file in self._filelist else None
        self.results = []
        self.emit("search-completed", last_pos, self._last_widget)

    def toggle_search_case(self):
        self._search_case = not self._search_case

    def toggle_incsearch(self):
        self._incsearch = not self._incsearch


# Initiate signals for the Search class
GObject.signal_new("search-completed", Search, GObject.SIGNAL_RUN_LAST,
                   None, (GObject.TYPE_PYOBJECT, GObject.TYPE_STRING))
GObject.signal_new("no-search-results", Search, GObject.SIGNAL_RUN_LAST,
                   None, (GObject.TYPE_PYOBJECT,))
