#!/usr/bin/env python
# encoding: utf-8
"""Contains the commandline class for vimiv."""
import re
import os
from threading import Thread
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from vimiv.fileactions import populate
from vimiv.helpers import read_file


class CommandLine(object):
    """Commandline of vimiv.

    Attributes:
        app: The main vimiv application to interact with.
        entry: Gtk.Entry as commandline entry.
        info: Gtk.Label to show completion information.
        history: List of commandline history to save.
        pos: Position in history completion.
        sub_history: Parts of the history that match entered text.
        search_positions: Search results as positions.
        search_case: If True, search case sensitively.
        incsearch: If True, enable incremental search in the library.
        last_filename: File that was last selected in the library, if any.
        running_threads: List of all running threads.
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
        self.entry.connect("changed", self.reset_tab_count)
        self.entry.set_hexpand(True)
        self.info = Gtk.Label()
        self.info.set_ellipsize(Pango.EllipsizeMode.END)
        padding = self.app.settings["GENERAL"]["commandline_padding"]
        self.info.set_margin_left(padding)
        self.info.set_margin_right(padding)
        self.info.set_margin_bottom(padding)

        # Monospaced font
        self.info.set_name("CompletionInfo")
        completion_provider = Gtk.CssProvider()
        completion_css = "#CompletionInfo { font-family: monospace; }".encode()
        completion_provider.load_from_data(completion_css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), completion_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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
        self.last_filename = ""
        self.running_threads = []

    def handler(self, entry):
        """Handle input from the entry.

        Check for type of command (internal, external, path or alias) and run
        the correct function.

        Args:
            entry: The Gtk.Entry from which the command comes.
        """
        # Only close completions if currently tabbing through results
        if self.app["completions"].cycling:
            self.app["completions"].reset()
            self.info.hide()
            return
        # cmd from input
        command = entry.get_text()
        # Check for alias and update command
        if command[1:] in self.app.aliases.keys():
            command = ":" + self.app.aliases[command[1:]]
        # And close the cmd line
        self.reset_text()
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
                self.app["keyhandler"].num_str = ""  # Used to repeat commands
                while cmd[0].isdigit():
                    self.app["keyhandler"].num_str += cmd[0]
                    cmd = cmd[1:]
                self.run_command(cmd)
        # Save the cmd to the history list avoiding duplicates
        if command in self.history:
            self.history.remove(command)
        self.history.insert(0, command)
        self.pos = 0

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
            self.app["statusbar"].err_message(err)
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
        # TODO make this cleaner
        try:
            fil = self.app.get_pos(True)
        except:
            return cmd
        # Check on which file(s) % and * should operate
        if self.app["mark"].marked:  # Always use marked files if they exist
            filelist = list(self.app["mark"].marked)
        elif self.app["window"].last_focused == "lib":
            filelist = list(self.app["library"].files)
        elif self.app["window"].last_focused in ["thu", "im"]:
            filelist = list(self.app.paths)
        else:  # Empty filelist as a fallback
            filelist = []
        # Only do substitution if a filelist exists
        if filelist:
            # Escape spaces for the shell
            fil = fil.replace(" ", "\\\\\\\\ ")
            for i, f in enumerate(filelist):
                filelist[i] = f.replace(" ", "\\\\\\\\ ")
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
            self.app["statusbar"].err_message("No input from pipe")
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
                self.app["image"].move_index(False, False, 0)
                # Close library if necessary
                if self.app["library"].grid.is_visible():
                    self.app["library"].toggle()
            elif old_pos:  # Nothing found, go back
                self.app.paths, self.app.index = populate(old_pos)
                self.app["statusbar"].err_message("No image found")
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
                self.app["window"].last_focused = "lib"
            else:
                # If it is an image open it
                self.app.paths = []
                self.app.paths, index = populate([path])
                self.app.index = 0
                self.app["image"].move_index(True, False, index)
                #  Reload library in lib mode, do not open it in image mode
                pathdir = os.path.dirname(path)
                if self.app["window"].last_focused == "lib":
                    self.app["library"].move_up(pathdir)
                    # Focus it in the treeview so it can be accessed via "l"
                    for i, fil in enumerate(self.app["library"].files):
                        if fil in path:
                            self.app["library"].treeview.set_cursor(
                                Gtk.TreePath(i), None, False)
                            break
                    # Show the image
                    self.app["library"].scrollable_treeview.set_hexpand(False)
                    self.app["image"].scrolled_win.show()
                else:
                    self.app["library"].move_up(pathdir, True)
        else:
            self.app["statusbar"].err_message("Warning: Not a valid path")

    def run_command(self, cmd):
        """Run the correct internal command.

        Args:
            cmd: Internal command to run.
        """
        parts = cmd.split()
        if "set" in cmd:
            given_args = parts[2:]
            cmd = " ".join(parts[:2])
        else:
            given_args = parts[1:]
            cmd = parts[0]
        # Check if the command exists
        if cmd in self.app.commands.keys():  # Run it
            function = self.app.commands[cmd][0]
            default_args = self.app.commands[cmd][1:]
            args = default_args + given_args
            # Check for wrong arguments
            try:
                function(*args)
            except TypeError as e:
                self.app["statusbar"].err_message(str(e))
            except SyntaxError:
                err = ("SyntaxError: are all strings closed " +
                       "and special chars quoted?")
                self.app["statusbar"].err_message(err)
            except NameError as e:
                argstr = "('" + args + "')"
                args = "(" + args + ")"
                function = function.replace(args, argstr)
                exec(function)
        else:  # Throw an error if the command does not exist
            self.app["statusbar"].err_message("No such command: %s" % (cmd))

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

    def focus(self):
        """Open and focus the command line."""
        # Colon for text
        self.entry.set_text(":")
        # Remove old error messages
        self.app["statusbar"].update_info()
        # Show/hide the relevant stuff
        self.entry.show()
        # Remember what widget was focused before
        if self.app["library"].treeview.is_focus():
            # In the library remember current file to refocus if incsearch was
            # not applied
            try:
                last_path = self.app["library"].treeview.get_cursor()[0]
                last_index = last_path.get_indices()[0]
                self.last_filename = self.app["library"].files[last_index]
            # Only works if there is a filelist
            except:
                self.last_filename = ""
            self.app["window"].last_focused = "lib"
        elif self.app["manipulate"].scrolled_win.is_visible():
            self.app["window"].last_focused = "man"
        elif self.app["thumbnail"].toggled:
            self.app["window"].last_focused = "thu"
        else:
            self.app["window"].last_focused = "im"
        self.entry.grab_focus()
        self.entry.set_position(-1)

    def reset_text(self):
        """Empty info and entry text to close the commandline.

        Trigger check_close() and therefore leave()
        """
        self.info.set_text("")
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

    def leave(self):
        """Apply actions to close the commandline."""
        self.entry.hide()
        self.info.hide()
        # Refocus the remembered widget
        if self.app["window"].last_focused == "lib":
            self.app["library"].focus(True)
        elif self.app["window"].last_focused == "man":
            self.app["manipulate"].scale_bri.grab_focus()
        elif self.app["window"].last_focused == "thu":
            self.app["thumbnail"].iconview.grab_focus()
        else:
            self.app["image"].scrolled_win.grab_focus()
        self.last_filename = ""

    def reset_tab_count(self, entry):
        """Reset the amount of tab presses if new text is entered.

        Args:
            entry: The Gtk.Entry to check.
        """
        self.app["completions"].tab_presses = 0
        self.app["completions"].cycling = False
        self.info.hide()

    def incremental_search(self, entry):
        """Run a search for every entered character.

        Args:
            entry: The Gtk.Entry to check.
        """
        text = entry.get_text()
        if (not self.app["window"].last_focused == "lib"
                and not self.app["window"].last_focused == "thu") \
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
        if self.app["window"].last_focused == "lib":
            paths = self.app["library"].files
        else:
            paths = [os.path.basename(path) for path in self.app.paths]

        # Fill search_positions with matching files depending on search_case
        self.search_positions = \
            [paths.index(fil) for fil in paths
             if searchstr in fil
             or not self.search_case and searchstr.lower() in fil.lower()]

        # Reload library and thumbnails to show search results
        if self.app["window"].last_focused == "lib":
            self.app["library"].reload(os.getcwd(), self.last_filename,
                                       search=True)
        elif self.app["window"].last_focused == "thu":
            # Reload all thumbnails in incsearch, only some otherwise
            if incsearch:
                self.app["thumbnail"].iconview.grab_focus()
                for index, thumb in enumerate(self.app["thumbnail"].elements):
                    self.app["thumbnail"].reload(thumb, index, False)
            else:
                for index in self.search_positions:
                    self.app["thumbnail"].reload(
                        self.app["thumbnail"].elements[index], index, False)

        # Move to first result or throw an error
        if self.search_positions:
            self.search_move(incsearch=incsearch)
        elif incsearch:
            self.entry.grab_focus()
            self.entry.set_position(-1)
        else:
            self.app["statusbar"].err_message("No matching file")

    def search_move(self, forward=True, incsearch=False):
        """Move to the next or previous search.

        Args:
            forward: If true, move forwards. Else move backwards.
            incsearch: If true, running from incsearch.
        """
        pos = self.app.get_pos()
        next_pos = 0
        # Correct handling of index
        if self.app["keyhandler"].num_str:
            index = int(self.app["keyhandler"].num_str)
            self.app["keyhandler"].num_str = ""
        else:
            index = 1
        # If backwards act on inverted list
        search_list = list(self.search_positions)
        if not forward:
            search_list.reverse()
        # Find next match depending on current position
        for i, search_pos in enumerate(search_list):
            if search_pos > pos and forward or search_pos < pos and not forward:
                next_pos = search_list[(i + index - 1) % len(search_list)]
                break
            elif search_pos == pos:
                next_pos = search_list[(i + index) % len(search_list)]
                break
            # Correctly wrap when on last element
            if search_pos == search_list[-1]:
                next_pos = search_list[0]

        # Select new file in library, image or thumbnail
        last_focused = self.app["window"].last_focused
        if last_focused == "lib":
            self.app["library"].treeview.set_cursor(Gtk.TreePath(next_pos),
                                                    None, False)
            self.app["library"].treeview.scroll_to_cell(Gtk.TreePath(next_pos),
                                                        None, True, 0.5, 0)
            # Auto select single file
            if len(self.search_positions) == 1 and not self.incsearch:
                self.app["library"].file_select(
                    self.app["library"].treeview, Gtk.TreePath(next_pos), None,
                    False)
        elif last_focused == "im":
            self.app["keyhandler"].num_str = str(next_pos + 1)
            self.app["image"].move_pos()
        elif self.app["window"].last_focused == "thu":
            self.app["thumbnail"].move_to_pos(next_pos)
        # Refocus entry if incsearch is appropriate
        if incsearch and not self.app["window"].last_focused == "im":
            self.entry.grab_focus()
            self.entry.set_position(-1)

    def reset_search(self):
        """Reset all search parameters to null."""
        self.search_positions = []

    def alias(self, alias, *command):
        """Add an alias.

        Args:
            alias: The alias to set up.
            command: Command to be called.
        """
        self.app.aliases[alias] = " ".join(command)
