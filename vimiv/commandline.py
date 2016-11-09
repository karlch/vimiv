#!/usr/bin/env python
# encoding: utf-8
"""Contains the commandline class for vimiv."""
import re
import os
from threading import Thread
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from vimiv.fileactions import populate
from vimiv.helpers import read_file

# Directories
vimivdir = os.path.expanduser("~/.vimiv")
tagdir = os.path.join(vimivdir, "Tags")


class CommandLine(object):
    """Commandline of vimiv.

    Attributes:
        vimiv: The main vimiv class to interact with.
        grid: Gtdk.Grid which packs the other objects.
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

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Command line
        self.grid = Gtk.Grid()
        self.entry = Gtk.Entry()
        self.entry.connect("activate", self.handler)
        self.entry.connect("key_press_event",
                           self.vimiv.keyhandler.run, "COMMAND")
        self.entry.connect("changed", self.check_close)
        self.entry.connect("changed", self.reset_tab_count)
        self.entry.set_hexpand(True)
        self.info = Gtk.Label()
        self.info.set_hexpand(True)
        self.info.set_valign(Gtk.Align.CENTER)
        self.info.set_halign(Gtk.Align.START)
        self.grid.attach(self.info, 0, 0, 1, 1)
        self.grid.attach(self.entry, 0, 1, 1, 1)
        # Make it nice using CSS
        self.grid.set_name("CommandLine")
        style = self.vimiv.get_style_context()
        color = style.get_background_color(Gtk.StateType.NORMAL)
        color_str = "#CommandLine { background-color: " + color.to_string() \
            + "; }"
        command_provider = Gtk.CssProvider()
        command_css = color_str.encode()
        command_provider.load_from_data(command_css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), command_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Alignment and spacing
        self.grid.set_valign(Gtk.Align.END)
        self.info.set_margin_top(6)
        self.info.set_margin_bottom(6)

        # Monospaced font
        self.info.set_name("CompletionInfo")
        completion_provider = Gtk.CssProvider()
        completion_css = "#CompletionInfo { font-family: monospace; }".encode()
        completion_provider.load_from_data(completion_css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), completion_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Cmd history from file
        self.history = read_file(os.path.expanduser("~/.vimiv/history"))

        # Defaults
        self.pos = 0
        self.sub_history = []
        self.search_positions = []
        self.search_case = general["search_case_sensitive"]
        self.incsearch = general["incsearch"]
        if self.incsearch:
            self.entry.connect("changed", self.incremental_search)
        self.last_filename = ""

        # List of threads
        self.running_threads = []

    def handler(self, entry):
        """Handle input from the entry.

        Check for type of command (internal, external, path or alias) and run
        the correct function.

        Args:
            entry: The Gtk.Entry from which the command comes.
        """
        # Only close completions if the tabbing is open
        if self.vimiv.completions.cycling:
            self.vimiv.completions.reset()
            self.info.hide()
            return
        # cmd from input
        command = entry.get_text()
        # Check for alias and update command
        if command[1:] in self.vimiv.aliases.keys():
            command = ":" + self.vimiv.aliases[command[1:]]
        # And close the cmd line
        if command[0] == "/":  # Search
            self.leave(True)
            if not self.incsearch or not self.vimiv.library.treeview.is_focus():
                self.search(command.lstrip("/"))
        else:  # Run a command
            self.leave()
            cmd = command.lstrip(":")
            # If there was no command just leave
            if not cmd:
                return
            # Parse different starts
            if cmd[0] == "!":
                self.run_external_command(cmd)
            elif cmd[0] == "~" or cmd[0] == "." or cmd[0] == "/":
                self.run_path(cmd)
            else:
                self.vimiv.keyhandler.num_str = ""  # Be able to repeat commands
                while True:
                    try:
                        num = int(cmd[0])
                        self.vimiv.keyhandler.num_str = \
                            self.vimiv.keyhandler.num_str + str(num)
                        cmd = cmd[1:]
                    except:
                        break
                self.run_command(cmd)
        # Save the cmd to a list
        if command in self.history:
            self.history.remove(command)
        self.history.insert(0, command)
        self.pos = 0

    def run_external_command(self, cmd):
        """Run the entered command in the terminal.

        Args:
            cmd: The command to run.
        """
        # Check on which file(s) % and * should operate
        if self.vimiv.window.last_focused == "lib" and self.vimiv.library.files:
            filelist = self.vimiv.library.files
            fil = self.vimiv.get_pos(True)
        elif self.vimiv.paths:
            filelist = self.vimiv.paths
            fil = self.vimiv.paths[self.vimiv.index]
        else:
            filelist = []
            fil = ""
        # Always operate on marked files if they exist
        if self.vimiv.mark.marked:
            filelist = self.vimiv.mark.marked
        # Escape spaces for the shell
        fil = fil.replace(" ", "\\\\\\\\ ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace(" ", "\\\\\\\\ ")
        cmd = cmd[1:]
        # Substitute % and * with escaping
        cmd = re.sub(r'(?<!\\)(%)', fil, cmd)
        cmd = re.sub(r'(?<!\\)(\*)', " ".join(filelist), cmd)
        cmd = re.sub(r'(\\)(?!\\)', '', cmd)
        # Run the command in an extra thread
        directory = os.getcwd()
        cmd_thread = Thread(target=self.thread_for_external, args=(cmd,
                                                                   directory))
        self.running_threads.append(cmd_thread)
        cmd_thread.start()
        # Undo the escaping
        fil = fil.replace("\\\\\\\\ ", " ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace("\\\\\\\\ ", " ")

    def thread_for_external(self, cmd, directory):
        """Start a new thread for external commands.

        Args:
            cmd: The command to run.
            directory: Directory which is affected by command.
        """
        try:
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
                self.vimiv.statusbar.err_message(err)
            else:
                GLib.timeout_add(1, self.vimiv.fileextras.reload_changes,
                                 directory, True, from_pipe, out)
            # Reload everything after an external command if we haven't moved,
            # you never know what happend ...
            # Must be in a timer because not all Gtk stuff can be accessed from
            # an external thread
        except FileNotFoundError as e:
            e = str(e)
            cmd = e.split()[-1]
            self.vimiv.statusbar.err_message("Command %s not found" % (cmd))
        self.running_threads.pop()

    def pipe(self, pipe_input):
        """Run output of external command in a pipe.

        This checks for directories, files and vimiv commands.

        Args:
            pipe_input: Command that comes from pipe.
        """
        # Leave if no pipe_input came
        if not pipe_input:
            self.vimiv.statusbar.err_message("No pipe_input from pipe")
            return
        # Make the pipe_input a file
        pipe_input = pipe_input.decode('utf-8')
        # List of commands without empty line
        pipe_input = pipe_input.split("\n")[:-1]
        startout = pipe_input[0]
        # Do different stuff depending on the first line of pipe_input
        if os.path.isdir(startout):
            self.vimiv.library.move_up(startout)
        elif os.path.isfile(startout):
            # Remember oldfile if no image was in filelist
            if self.vimiv.paths:
                old_pos = [self.vimiv.paths[self.vimiv.index]]
                self.vimiv.paths = []
            else:
                old_pos = []
            # Populate filelist
            self.vimiv.paths, self.vimiv.index = populate(pipe_input)
            if self.vimiv.paths:  # Images were found
                self.vimiv.image.scrolled_win.show()
                self.vimiv.image.move_index(False, False, 0)
                # Close library if necessary
                if self.vimiv.library.grid.is_visible():
                    self.vimiv.library.toggle()
            elif old_pos:  # Nothing found, go back
                self.vimiv.paths, self.vimiv.index = populate(old_pos)
                self.vimiv.statusbar.err_message("No image found")
        else:
            # Run every line as an internal command
            for cmd in pipe_input:
                self.run_command(cmd)

    def run_path(self, path):
        """Run a path command, namely populate files or focus directory.

        Args:
            path: The path to run on.
        """
        # Expand home
        if path[0] == "~":
            path = os.path.expanduser("~") + path[1:]
        try:
            path = os.path.abspath(path)
            if not os.path.exists(path):
                raise ValueError
            elif os.path.isdir(path):
                self.vimiv.library.move_up(path)
                # If we open the library it must be focused as well
                self.vimiv.window.last_focused = "lib"
            else:
                # If it is an image open it
                self.vimiv.paths = []
                self.vimiv.paths, index = populate([path])
                self.vimiv.index = 0
                self.vimiv.image.move_index(True, False, index)
                #  Reload library in lib mode, do not open it in image mode
                abspath = os.path.dirname(path)
                if self.vimiv.window.last_focused == "lib":
                    self.vimiv.library.move_up(abspath)
                    # Focus it in the treeview so it can be accessed via "l"
                    for i, fil in enumerate(self.vimiv.library.files):
                        if fil in path:
                            self.vimiv.library.treeview.set_cursor(
                                Gtk.TreePath(i), None, False)
                            break
                    # Show the image
                    self.vimiv.library.scrollable_treeview.set_size_request(
                        self.vimiv.library.width, 10)
                    self.vimiv.image.scrolled_win.show()
                else:
                    self.vimiv.library.move_up(abspath, True)
        except:
            self.vimiv.statusbar.err_message("Warning: Not a valid path")

    def run_command(self, cmd):
        """Run the correct internal command.

        Args:
            cmd: Internal command to run.
        """
        parts = cmd.split()
        if "set" in cmd:
            arg = parts[2:]
            cmd = " ".join(parts[:2])
        else:
            arg = parts[1:]
            cmd = parts[0]
        # Check if the command exists
        if cmd in self.vimiv.commands.keys():  # Run it
            function = self.vimiv.commands[cmd][0]
            default_args = self.vimiv.commands[cmd][1:]
            arg = default_args + arg
            # Check for wrong arguments
            try:
                if arg:
                    function(*arg)
                else:
                    function()
            except TypeError as e:
                self.vimiv.statusbar.err_message(str(e))
            except SyntaxError:
                err = ("SyntaxError: are all strings closed " +
                       "and special chars quoted?")
                self.vimiv.err_message(err)
            except NameError as e:
                argstr = "('" + arg + "')"
                arg = "(" + arg + ")"
                function = function.replace(arg, argstr)
                exec(function)
        else:  # Throw an error if the command does not exist
            self.vimiv.statusbar.err_message("No such command: %s" % (cmd))

    def history_search(self, down):
        """Search through history with substring match.

        Updates the text of self.entry with the matching history search.

        Args:
            down: If True, search downwards. Else search updwards.
        """
        # Shortly disconnect the change signal
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
        self.pos = self.pos % (len(self.sub_history))
        self.entry.set_text(self.sub_history[self.pos])
        self.entry.set_position(-1)
        # Reconnect when done
        self.entry.connect("changed", self.check_close)

    def focus(self):
        """Open and focus the command line."""
        # Colon for text
        self.entry.set_text(":")
        # Remove old error messages
        self.vimiv.statusbar.update_info()
        # Show/hide the relevant stuff
        self.grid.show()
        # Remember what widget was focused before
        if self.vimiv.library.treeview.is_focus():
            # In the library remember current file to refocus if incsearch was
            # not applied
            try:
                last_path = self.vimiv.library.treeview.get_cursor()[0]
                last_index = last_path.get_indices()[0]
                self.last_filename = self.vimiv.library.files[last_index]
            # Only works if there is a filelist
            except:
                self.last_filename = ""
            self.vimiv.window.last_focused = "lib"
        elif self.vimiv.manipulate.scrolled_win.is_visible():
            self.vimiv.window.last_focused = "man"
        elif self.vimiv.thumbnail.toggled:
            self.vimiv.window.last_focused = "thu"
        else:
            self.vimiv.window.last_focused = "im"
        self.entry.grab_focus()
        self.entry.set_position(-1)

    def leave(self, search=False):
        """Close the command line."""
        self.grid.hide()
        # Remove all completions shown and the text currently inserted
        self.info.set_text("")
        self.entry.set_text("")
        if not search:
            self.reset_search()
        # Refocus the remembered widget
        if self.vimiv.window.last_focused == "lib":
            if not search:
                self.vimiv.library.reload(".", self.last_filename)
            self.vimiv.library.focus(True)
        elif self.vimiv.window.last_focused == "man":
            self.vimiv.manipulate.scale_bri.grab_focus()
        elif self.vimiv.window.last_focused == "thu":
            self.vimiv.thumbnail.iconview.grab_focus()
        else:
            self.vimiv.image.scrolled_win.grab_focus()
        self.last_filename = ""

    def check_close(self, entry):
        """Close the entry if the colon/slash is deleted.

        Args:
            entry: The Gtk.Entry to check.
        """
        self.sub_history = []
        self.pos = 0
        text = entry.get_text()
        if not text or text[0] not in ":/":
            self.leave(True)

    def reset_tab_count(self, entry):
        """Reset the amount of tab presses if new text is entered.

        Args:
            entry: The Gtk.Entry to check.
        """
        self.vimiv.completions.tab_presses = 0
        self.vimiv.completions.cycling = False
        self.info.hide()

    def incremental_search(self, entry):
        """Run a search for every entered character.

        Args:
            entry: The Gtk.Entry to check.
        """
        text = entry.get_text()
        if not self.vimiv.window.last_focused == "lib" or len(text) < 2:
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
        """
        if self.vimiv.window.last_focused == "lib":
            paths = self.vimiv.library.files
        else:
            paths = [os.path.basename(path) for path in self.vimiv.paths]
        self.search_positions = []

        if self.search_case:
            for i, fil in enumerate(paths):
                if searchstr in fil:
                    self.search_positions.append(i)
        else:
            for i, fil in enumerate(paths):
                if searchstr.lower() in fil.lower():
                    self.search_positions.append(i)

        if self.vimiv.window.last_focused == "lib":
            self.vimiv.library.reload(os.getcwd(), self.last_filename, search=True)

        # Move to first result or throw an error
        if self.search_positions:
            self.search_move(incsearch=incsearch)
        else:
            self.vimiv.statusbar.err_message("No matching file")

    def search_move(self, forward=True, incsearch=False):
        """Move to the next or previous search.

        Args:
            forward: If true, move forwards. Else move backwards.
            incsearch: If true, running from incsearch.
        """
        pos = self.vimiv.get_pos()
        next_pos = 0
        # Correct handling of index
        if self.vimiv.keyhandler.num_str:
            index = int(self.vimiv.keyhandler.num_str)
            self.vimiv.keyhandler.num_str = ""
        else:
            index = 1
        # If backwards act on inverted list
        if forward:
            search_list = self.search_positions
        else:
            search_list = self.search_positions[::-1]
        # Find next match depending on current position
        for i, search_pos in enumerate(search_list):
            if search_pos > pos and forward or search_pos < pos and not forward:
                next_pos = search_list[(i + index - 1) % len(search_list)]
                break
            elif search_pos == pos:
                next_pos = search_list[(i + index) % len(search_list)]
                break

        # Select new file in library or image
        if self.vimiv.library.grid.is_visible():
            self.vimiv.library.treeview.set_cursor(Gtk.TreePath(next_pos),
                                                   None, False)
            if len(self.search_positions) == 1 and not self.incsearch:
                self.vimiv.library.file_select(self.vimiv.library.treeview,
                                               Gtk.TreePath(next_pos),
                                               None,
                                               False)
            if incsearch:
                self.entry.grab_focus()
        else:
            self.vimiv.keyhandler.num_str = str(next_pos + 1)
            self.vimiv.image.move_pos()


    def reset_search(self):
        """Reset all search parameters to null."""
        self.search_positions = []

    def alias(self, alias, *command):
        """Add an alias.

        Args:
            alias: The alias to set up.
            command: Command to be called.
        """
        self.vimiv.aliases[alias] = " ".join(command)
