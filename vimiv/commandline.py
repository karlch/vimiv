# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains the commandline class for vimiv."""
import re
import os
from bisect import bisect_left, bisect_right
from threading import Thread
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from vimiv.fileactions import populate
from vimiv.helpers import read_file


class CommandLine(object):
    """Commandline of vimiv.

    Attributes:
        app: The main vimiv application to interact with.
        entry: Gtk.Entry as commandline entry.
        history: List of commandline history to save.
        pos: Position in history completion.
        sub_history: Parts of the history that match entered text.
        search_positions: Search results as positions.
        search_case: If True, search case sensitively.
        incsearch: If True, enable incremental search in the library.
        last_index: Index that was last selected in the library, if any.
        running_threads: List of all running threads.
        last_focused: Widget that was focused before the command line.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
            settings: Settings from configfiles to use.
        """
        self.app = app
        general = settings["GENERAL"]

        # Command line
        self.entry = Gtk.Entry()
        self.entry.connect("activate", self.handler)
        self.entry.connect("key_press_event",
                           self.app["keyhandler"].run, "COMMAND")
        self.entry.connect("changed", self.check_close)
        self.entry.set_hexpand(True)

        # Cmd history from file
        self.history = read_file(os.path.join(self.app.directory, "history"))

        # Defaults
        self.pos = 0
        self.sub_history = []
        self.search_positions = []
        self.search_case = general["search_case_sensitive"]
        self.incsearch = general["incsearch"]
        if self.incsearch:
            self.entry.connect("changed", self.incremental_search)
        self.last_index = 0
        self.running_threads = []
        self.last_focused = ""

    def handler(self, entry):
        """Handle input from the entry.

        Check for type of command (internal, external, path or alias) and run
        the correct function.

        Args:
            entry: The Gtk.Entry from which the command comes.
        """
        # Only close completions if currently tabbing through results
        if self.app["completions"].tab_presses != 0:
            self.app["completions"].activate(None, None, None)
            self.app["completions"].reset()
            return
        # cmd from input
        command = entry.get_text()
        # Check for alias and update command
        if command[1:] in self.app.aliases:
            command = ":" + self.app.aliases[command[1:]]
        # And close the cmd line
        self.reset_text()
        # Write command to log in debug mode
        if self.app.debug:
            self.app["log"].write_message("commandline", command)
        # Save the cmd to the history list avoiding duplicates
        if command in self.history:
            self.history.remove(command)
        self.history.insert(0, command)
        # Reset history position
        self.pos = 0
        # Run the correct command
        self.run(command)

    def run(self, command):
        """Run correct function for command.

        Calls one of search, run_external_command, run_path and run_command.

        Args:
            command: The command to operate on.
        """
        if command[0] == "/":  # Search
            # Do not search again if incsearch was running
            if not (self.app["library"].treeview.is_focus() or
                    self.app["thumbnail"].iconview.is_focus()) or \
                    not self.incsearch:
                self.search(command.lstrip("/"))
            # Auto select single file in the library
            elif self.incsearch and len(self.search_positions) == 1 and \
                    self.app["library"].treeview.is_focus():
                self.app["library"].file_select(
                    self.app["library"].treeview,
                    Gtk.TreePath(self.app.get_pos()), None, False)
        else:  # Run a command
            cmd = command.lstrip(":")
            # If there was no command just leave
            if not cmd:
                return
            # Run something different depending on first char in cmd
            if cmd[0] == "!":
                self.run_external_command(cmd)
            elif cmd[0] == "~" or cmd[0] == "." or cmd[0] == "/":
                self.run_path(cmd)
            else:  # Default to internal cmd
                self.app["keyhandler"].num_clear()
                while cmd[0].isdigit():
                    self.app["keyhandler"].num_str += cmd[0]
                    cmd = cmd[1:]
                self.run_command(cmd)

    def run_external_command(self, cmd):
        """Run the entered command in the terminal.

        Args:
            cmd: The command to run.
        """
        cmd = self.expand_filenames(cmd)
        # Run the command in an extra thread, useful e.g. for gimp %
        directory = os.getcwd()
        cmd_thread = Thread(target=self.thread_for_external, args=(cmd,
                                                                   directory))
        self.running_threads.append(cmd_thread)
        cmd_thread.start()

    def thread_for_external(self, cmd, directory):
        """Start a new thread for external commands.

        Args:
            cmd: The command to run.
            directory: Directory which is affected by command.
        """
        # Possibility to "pipe to vimiv"
        if cmd[-1] == "|":
            cmd = cmd.rstrip("|")
            p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            from_pipe = True
        else:
            p = Popen(cmd, stderr=PIPE, shell=True)
            from_pipe = False
        # Get output and error and run the command
        out, err = p.communicate()
        if p.returncode:
            err = err.decode('utf-8').split("\n")[0]
            self.app["statusbar"].message(err, "error")
        else:
            # Reload everything after an external command if we haven't
            # moved, you never know what happened ... Must be in a timer
            # because not all Gtk stuff can be accessed from an external
            # thread.
            # Only reload paths if the path directory or any file was in the
            # command
            reload_path = False
            if os.path.basename(os.getcwd()) in cmd or \
                    [fil for fil in self.app.paths
                     if os.path.basename(fil) in cmd]:
                reload_path = True
            GLib.timeout_add(1, self.app["fileextras"].reload_changes,
                             directory, reload_path, from_pipe, out)
        self.running_threads.pop()

    def expand_filenames(self, cmd):
        """Expand % and * for the command to run.

        Args:
            cmd: The command to run.
        """
        fil = self.app.get_pos(True)
        # Check on which file(s) % and * should operate
        if self.app["mark"].marked:  # Always use marked files if they exist
            filelist = list(self.app["mark"].marked)
        elif self.last_focused == "lib":
            filelist = list(self.app["library"].files)
        elif self.last_focused in ["thu", "im"]:
            filelist = list(self.app.paths)
        else:  # Empty filelist as a fallback
            filelist = []
        # Only do substitution if a filelist exists
        if filelist:
            # Escape spaces for the shell
            fil = fil.replace(" ", "\\\\\\\\ ")
            filelist = [f.replace(" ", "\\\\\\\\ ") for f in filelist]
            cmd = cmd[1:]
            # Substitute % and * with escaping
            cmd = re.sub(r'(?<!\\)(%)', fil, cmd)
            cmd = re.sub(r'(?<!\\)(\*)', " ".join(filelist), cmd)
            cmd = re.sub(r'(\\)(?!\\)', '', cmd)
        return cmd

    def pipe(self, pipe_input):
        """Run output of external command in a pipe.

        This checks for directories, files and vimiv commands.

        Args:
            pipe_input: Command that comes from pipe.
        """
        # Leave if no pipe_input came
        if not pipe_input:
            self.app["statusbar"].message("No input from pipe", "info")
            return
        # Make the pipe_input a file
        pipe_input = pipe_input.decode('utf-8')
        # List of commands without empty line
        pipe_input = pipe_input.split("\n")[:-1]
        startout = pipe_input[0]
        # Do different stuff depending on the first line of pipe_input
        if os.path.isdir(startout):
            self.app["library"].move_up(startout)
        elif os.path.isfile(startout):
            # Remember old file if no image was in filelist
            if self.app.paths:
                old_pos = [self.app.paths[self.app.index]]
                self.app.paths = []
            else:
                old_pos = []
            # Populate filelist
            self.app.paths, self.app.index = populate(pipe_input)
            if self.app.paths:  # Images were found
                self.app["image"].scrolled_win.show()
                self.app["image"].load_image()
                # Close library if necessary
                if self.app["library"].grid.is_visible():
                    self.app["library"].toggle()
            elif old_pos:  # Nothing found, go back
                self.app.paths, self.app.index = populate(old_pos)
                self.app["statusbar"].message("No image found", "info")
        else:  # Run every line as an internal command
            for cmd in pipe_input:
                self.run_command(cmd)

    def run_path(self, path):
        """Run a path command, namely populate files or focus directory.

        Args:
            path: The path to run on.
        """
        # Expand home and use absolute path
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.exists(path):
            if os.path.isdir(path):
                # Focus directory in the library
                self.app["library"].move_up(path)
                self.last_focused = "lib"
            else:
                # If it is an image open it
                self.app.paths = []
                self.app.paths, self.app.index = populate([path])
                self.app["image"].load_image()
                #  Reload library in lib mode, do not open it in image mode
                pathdir = os.path.dirname(path)
                if self.last_focused == "lib":
                    self.app["library"].move_up(pathdir)
                    # Focus it in the treeview so it can be accessed via "l"
                    index = \
                        self.app["library"].files.index(os.path.basename(path))
                    self.app["library"].treeview.set_cursor(
                        Gtk.TreePath(index), None, False)
                    # Show the image
                    self.app["library"].scrollable_treeview.set_hexpand(False)
                    self.app["image"].scrolled_win.show()
                else:
                    self.app["library"].move_up(pathdir, True)
        else:
            self.app["statusbar"].message("Not a valid path", "error")

    def run_command(self, cmd, keyname=None):
        """Run the correct internal command.

        Args:
            cmd: Internal command to run.
            keyname: Key that called run_command. Passed when called from
                keyhandler.
        """
        name_func_and_args = cmd.split()
        if cmd.startswith("set "):
            name_func = " ".join(name_func_and_args[0:2])
            conf_args = name_func_and_args[2:]
        else:
            name_func = name_func_and_args[0]
            conf_args = name_func_and_args[1:]
        # Get the actual dictionary from command or function dictionary
        # depending on whether called from command line or keyhandler
        func_dict = self.app.functions if keyname else self.app.commands
        if name_func in func_dict:
            func_and_args = func_dict[name_func]
            func = func_and_args[0]
            default_args = func_and_args[1]
            # Check if the amount of arguments
            required_args = func_and_args[2]
            optional_args = func_and_args[3]
            args = default_args + conf_args
            if len(conf_args) < len(required_args):
                message = "Missing positional arguments for command " + \
                    name_func + ": " + ", ".join(required_args)
                self.app["statusbar"].message(message, "error")
            elif len(conf_args) > len(required_args) + len(optional_args):
                message = "Too many arguments for command " + name_func
                self.app["statusbar"].message(message, "error")
            else:
                func(*args)
        # If the command name is not in the dictionary throw an error
        else:
            message = "No command called " + name_func
            if keyname:
                message += " bound to " + keyname
            self.app["statusbar"].message(message, "error")

    def history_search(self, down):
        """Search through history with substring match.

        Updates the text of self.entry with the matching history search.

        Args:
            down: If True, search downwards. Else search upwards.
        """
        # Shortly disconnect the change signal as it resets the history search
        self.entry.disconnect_by_func(self.check_close)
        # Only parts of the history that match the entered text
        if not self.sub_history:
            substring = self.entry.get_text()
            matchstr = '^(' + substring + ')'
            self.sub_history = [substring]
            for cmd in self.history:
                if re.match(matchstr, cmd):
                    self.sub_history.append(cmd)
        # Move and set the text
        if down:
            self.pos -= 1
        else:
            self.pos += 1
        self.pos = self.pos % len(self.sub_history)
        self.entry.set_text(self.sub_history[self.pos])
        self.entry.set_position(-1)
        # Reconnect when done
        self.entry.connect("changed", self.check_close)

    def focus(self, text=""):
        """Open and focus the command line."""
        # Colon for text
        self.entry.set_text(":" + text)
        # Show/hide the relevant stuff
        self.entry.show()
        self.app["completions"].show()
        # Remember what widget was focused before
        if self.app["library"].treeview.is_focus():
            # In the library remember current file to refocus if incsearch was
            # not applied
            self.last_focused = "lib"
        elif self.app["manipulate"].scrolled_win.is_visible():
            self.last_focused = "man"
        elif self.app["thumbnail"].toggled:
            self.last_focused = "thu"
        else:
            self.last_focused = "im"
        self.reset_search(leaving=False)
        self.entry.grab_focus()
        self.entry.set_position(-1)
        # Update info for command mode
        self.app["statusbar"].update_info()

    def reset_text(self):
        """Empty info and entry text to close the commandline.

        Trigger check_close() and therefore leave()
        """
        self.entry.set_text("")

    def check_close(self, entry):
        """Close the entry if the colon/slash is deleted.

        Args:
            entry: The Gtk.Entry to check.
        """
        self.sub_history = []
        self.pos = 0
        text = entry.get_text()
        if not text or text[0] not in ":/":
            self.leave()

    def leave(self, reset_search=False):
        """Apply actions to close the commandline."""
        self.app["completions"].treeview.scroll_to_point(0, 0)
        self.entry.hide()
        self.app["completions"].hide()
        self.app["completions"].reset()
        # Refocus the remembered widget
        if self.last_focused == "lib":
            self.app["library"].focus(True)
        elif self.last_focused == "man":
            self.app["manipulate"].sliders["bri"].grab_focus()
        elif self.last_focused == "thu":
            self.app["thumbnail"].iconview.grab_focus()
        else:
            self.app["image"].scrolled_win.grab_focus()
        if reset_search:
            self.reset_search(leaving=True)
        self.last_index = 0
        self.app["statusbar"].update_info()

    def incremental_search(self, entry):
        """Run a search for every entered character.

        Args:
            entry: The Gtk.Entry to check.
        """
        text = entry.get_text()
        if (not self.last_focused == "lib"
                and not self.last_focused == "thu") \
                or len(text) < 2:
            return
        elif text[0] == "/":
            self.search(text.lstrip("/"), True)

    def cmd_search(self):
        """Prepend search character '/' to the cmd_line and open it."""
        self.focus()
        self.entry.set_text("/")
        self.entry.set_position(-1)

    def search(self, searchstr, incsearch=False):
        """Run a search on the appropriate filelist.

        Args:
            searchstr: The search string to parse.
            incsearch: Do incremental search or not.
        """
        if self.last_focused == "lib":
            paths = self.app["library"].files
        else:
            paths = [os.path.basename(path) for path in self.app.paths]

        # Fill search_positions with matching files depending on search_case
        self.search_positions = \
            [paths.index(fil) for fil in paths
             if searchstr in fil
             or not self.search_case and searchstr.lower() in fil.lower()]

        # Reload library and thumbnails to show search results
        if self.last_focused == "lib":
            self.app["library"].focus(True)
            self.app["library"].reload_names()
        elif self.last_focused == "thu":
            # Reload all thumbnails in incsearch, only some otherwise
            if incsearch:
                self.app["thumbnail"].iconview.grab_focus()
                for image in self.app.paths:
                    self.app["thumbnail"].reload(image, False)
            else:
                for index in self.search_positions:
                    self.app["thumbnail"].reload(self.app.paths[index], False)

        # Move to first result or throw an error
        if self.search_positions:
            self.search_move_internal(incsearch)
        elif incsearch:
            self.entry.grab_focus()
            self.entry.set_position(-1)
        else:
            self.app["statusbar"].message("No matching file", "info")

    def search_move(self, forward=True):
        """Move to the next or previous search.

        Args:
            forward: If true, move forwards. Else move backwards.
        """
        if not self.search_positions:
            self.app["statusbar"].message("No search results", "warning")
            return
        # Correct handling of prefixed numbers
        if self.app["keyhandler"].num_str:
            add_on = int(self.app["keyhandler"].num_str) - 1
            self.app["keyhandler"].num_clear()
        else:
            add_on = 0
        # Next position depending on current position and direction
        pos = self.app.get_pos()
        if forward:
            index = bisect_right(self.search_positions, pos) + add_on
        else:
            index = bisect_left(self.search_positions, pos) - 1 - add_on
        next_pos = self.search_positions[index % len(self.search_positions)]
        self.file_select(next_pos, incsearch=False)

    def search_move_internal(self, incsearch=False):
        """Select the first search match when called from search internally.

        Args:
            incsearch: Do incremental search or not.
        """
        pos = self.app.get_pos()
        index = bisect_left(self.search_positions, pos)
        next_pos = self.search_positions[index % len(self.search_positions)]
        self.file_select(next_pos, incsearch)

    def file_select(self, position, incsearch):
        """Select next file from search in library, image or thumbnail.

        Args:
            position: Position of the file to select.
            incsearch: Do incremental search or not.
        """
        # Select new file in library, image or thumbnail
        if self.last_focused == "lib":
            self.app["library"].treeview.set_cursor(Gtk.TreePath(position),
                                                    None, False)
            self.app["library"].treeview.scroll_to_cell(Gtk.TreePath(position),
                                                        None, True, 0.5, 0)
            # Auto select single file
            if len(self.search_positions) == 1 and not self.incsearch:
                self.app["library"].file_select(
                    self.app["library"].treeview, Gtk.TreePath(position), None,
                    False)
        elif self.last_focused == "im":
            self.app["keyhandler"].num_str = str(position + 1)
            self.app["image"].move_pos()
        elif self.last_focused == "thu":
            self.app["thumbnail"].move_to_pos(position)
        # Refocus entry if incsearch is appropriate
        if incsearch and not self.last_focused == "im":
            self.entry.grab_focus()
            self.entry.set_position(-1)

    def reset_search(self, leaving):
        """Reset all search parameters to null.

        Args:
            leaving: If True, leaving the commandline. Else entering.
        """
        self.search_positions = []
        # Remember position when entering
        if not leaving:
            self.last_index = self.app.get_pos()
        # Reload library or thumbnail
        if self.last_focused == "lib":
            self.app["library"].reload_names()
            if leaving:
                self.app["library"].treeview.set_cursor(
                    Gtk.TreePath(self.last_index), None, False)
                self.app["library"].treeview.scroll_to_cell(
                    Gtk.TreePath(self.last_index), None, True, 0.5, 0)
        elif self.last_focused == "thu":
            for image in self.app.paths:
                self.app["thumbnail"].reload(image, False)
            if leaving:
                self.app["thumbnail"].move_to_pos(self.last_index)

    def alias(self, alias, *command):
        """Add an alias.

        Args:
            alias: The alias to set up.
            command: Command to be called.
        """
        self.app.aliases[alias] = " ".join(command)
