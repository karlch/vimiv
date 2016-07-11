#!/usr/bin/env python
# encoding: utf-8
""" Contains the commandline class for vimiv """
import re
import os
from threading import Thread
from subprocess import Popen, PIPE
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango
from vimiv.fileactions import populate
from vimiv.helpers import read_file

# Directories
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
tagdir = os.path.join(vimivdir, "Tags")

class CommandLine(object):
    """ Commandline of vimiv """

    def __init__(self, vimiv, settings):
        self.vimiv = vimiv
        general = settings["GENERAL"]

        # Command line
        self.cmd_line_box = Gtk.HBox(False, 0)
        self.cmd_line = Gtk.Entry()
        self.cmd_line.connect("activate", self.cmd_handler)
        self.cmd_line.connect("key_press_event",
                              self.vimiv.keyhandler.handle_key_press, "COMMAND")
        self.cmd_line.connect("changed", self.cmd_check_close)
        self.cmd_line_info = Gtk.Label()
        self.cmd_line_info.set_max_width_chars(self.vimiv.winsize[0]/16)
        self.cmd_line_info.set_ellipsize(Pango.EllipsizeMode.END)
        self.cmd_line_box.pack_start(self.cmd_line, True, True, 0)
        self.cmd_line_box.pack_end(self.cmd_line_info, False, False, 0)

        # Cmd history from file
        self.cmd_history = read_file(os.path.expanduser("~/.vimiv/history"))

        # Defaults
        self.cmd_pos = 0
        self.sub_history = []
        self.search_pos = 0
        self.search_positions = []
        self.search_names = []
        self.search_case = general["search_case_insensitive"]

    def cmd_handler(self, entry):
        """ Handles input from the entry, namely if it is a path to be focused
        or a (external) command to be run """
        # cmd from input
        command = entry.get_text()
        # And close the cmd line
        self.cmd_line_leave()
        if command[0] == "/":  # Search
            self.search(command.lstrip("/"))
        else:  # Run a command
            cmd = command.lstrip(":")
            # If there was no command just leave
            if not cmd:
                return
            # Parse different starts
            if cmd[0] == "!":
                self.run_external_command(cmd)
            elif cmd[0] == "~" or cmd[0] == "." or cmd[0] == "/":
                self.cmd_path(cmd)
            else:
                self.vimiv.keyhandler.num_str = ""  # Be able to repeat commands
                while True:
                    try:
                        num = int(cmd[0])
                        self.vimiv.keyhandler.num_str = self.vimiv.keyhandler.num_str + str(num)
                        cmd = cmd[1:]
                    except:
                        break
                self.run_command(cmd)
        # Save the cmd to a list
        if command in self.cmd_history:
            self.cmd_history.remove(command)
        self.cmd_history.insert(0, command)
        self.cmd_pos = 0

    def run_external_command(self, cmd):
        """ Run the entered command in the terminal """
        # Check on which file(s) % and * should operate
        if self.vimiv.window.last_focused == "lib" and self.vimiv.library.files:
            filelist = self.vimiv.library.files
            fil = self.vimiv.library.files[self.vimiv.library.treepos]
        elif self.vimiv.paths:
            filelist = self.vimiv.paths
            fil = self.vimiv.paths[self.vimiv.index]
        else:
            filelist = []
            fil = ""
        if self.vimiv.mark.marked:  # Always operate on marked files if they exist
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
        directory = os.path.abspath(".")
        cmd_thread = Thread(target=self.thread_for_external, args=(cmd,
                                                                   directory))
        cmd_thread.start()
        # Undo the escaping
        fil = fil.replace("\\\\\\\\ ", " ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace("\\\\\\\\ ", " ")

    def thread_for_external(self, cmd, directory):
        """ Starting a new thread for external commands """
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
                self.vimiv.err_message(err)
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


    def pipe(self, pipe_input):
        """ Run output of external command in a pipe
            This checks for directories, files and vimiv commands """
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
                if self.vimiv.library.toggled:
                    self.vimiv.library.toggle_library()
            elif old_pos:  # Nothing found, go back
                self.vimiv.paths, self.vimiv.index = populate(old_pos)
                self.vimiv.statusbar.err_message("No image found")
        else:
            # Run every line as an internal command
            for cmd in pipe_input:
                self.run_command(cmd)


    def cmd_path(self, path):
        """ Run a path command, namely populate files or focus directory """
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
                            self.vimiv.library.treeview.set_cursor(Gtk.TreePath(i),
                                                        None, False)
                            self.vimiv.library.treepos = i
                            break
                    # Show the image
                    self.vimiv.library.grid.set_size_request(self.vimiv.library.library_width-
                                                self.vimiv.library.border_width, 10)
                    self.vimiv.image.scrolled_win.show()
                else:
                    self.vimiv.library.move_up(abspath, True)
        except:
            self.vimiv.statusbar.err_message("Warning: Not a valid path")

    def run_command(self, cmd):
        """ Run the correct internal cmd """
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
        else:  # Through an error
            self.vimiv.statusbar.err_message("No such command: %s" % (cmd))

    def history(self, down):
        """ Update the cmd_handler text with history """
        # Shortly disconnect the change signal
        self.cmd_line.disconnect_by_func(self.cmd_check_close)
        # Only parts of the history that match the entered text
        if not self.sub_history:
            substring = self.cmd_line.get_text()
            matchstr = '^(' + substring + ')'
            self.sub_history = [substring]
            for cmd in self.cmd_history:
                if re.match(matchstr, cmd):
                    self.sub_history.append(cmd)
        # Move and set the text
        if down:
            self.cmd_pos -= 1
        else:
            self.cmd_pos += 1
        self.cmd_pos = self.cmd_pos % (len(self.sub_history))
        self.cmd_line.set_text(self.sub_history[self.cmd_pos])
        self.cmd_line.set_position(-1)
        # Reconnect when done
        self.cmd_line.connect("changed", self.cmd_check_close)

    def focus_cmd_line(self):
        """ Open and focus the command line """
        # Colon for text
        self.cmd_line.set_text(":")
        # Show the statusbar
        if self.vimiv.statusbar.sbar:
            self.vimiv.bbox.show()
        # Remove old error messages
        self.vimiv.statusbar.update_info()
        # Show/hide the relevant stuff
        self.cmd_line_box.show()
        self.vimiv.statusbar.bar.hide()
        self.vimiv.bbox.set_border_width(10)
        # Remember what widget was focused before
        if self.vimiv.library.focused:
            self.vimiv.window.last_focused = "lib"
        elif self.vimiv.manipulate.toggled:
            self.vimiv.window.last_focused = "man"
        elif self.vimiv.thumbnail.toggled:
            self.vimiv.window.last_focused = "thu"
        else:
            self.vimiv.window.last_focused = "im"
        self.cmd_line.grab_focus()
        self.cmd_line.set_position(-1)

    def cmd_line_leave(self):
        """ Close the command line """
        self.cmd_line_box.hide()
        self.vimiv.statusbar.bar.show()
        self.vimiv.bbox.set_border_width(12)
        # Remove all completions shown and the text currently inserted
        self.cmd_line_info.set_text("")
        self.cmd_line.set_text("")
        # Refocus the remembered widget
        if self.vimiv.window.last_focused == "lib":
            self.vimiv.library.focus_library(True)
        elif self.vimiv.window.last_focused == "man":
            self.vimiv.manipulate.scale_bri.grab_focus()
        elif self.vimiv.window.last_focused == "thu":
            self.vimiv.thumbnail.iconview.grab_focus()
        else:
            self.vimiv.image.scrolled_win.grab_focus()
        # Rehide the command line
        if self.vimiv.statusbar.sbar:
            self.vimiv.bbox.hide()

    def cmd_check_close(self, entry):
        """ Close the entry if the colon/slash is deleted """
        self.sub_history = []
        self.cmd_pos = 0
        text = entry.get_text()
        if not text or text[0] not in ":/":
            self.cmd_line_leave()

    def cmd_search(self):
        """ Prepend search to the cmd_line and open it """
        self.focus_cmd_line()
        self.cmd_line.set_text("/")
        self.cmd_line.set_position(-1)

    def search(self, searchstr):
        """ Run a search on the appropriate filelist """
        if self.vimiv.library.focused:
            paths = self.vimiv.library.files
        else:
            paths = self.vimiv.paths
        self.search_names = []
        self.search_positions = []
        self.search_pos = 0

        if self.search_case:
            for i, fil in enumerate(paths):
                if searchstr in fil:
                    self.search_names.append(fil)
                    self.search_positions.append(i)
        else:
            for i, fil in enumerate(paths):
                if searchstr.lower() in fil.lower():
                    self.search_names.append(fil)
                    self.search_positions.append(i)

        if self.vimiv.library.focused:
            self.vimiv.library.reload(".", search=True)

        # Move to first result or throw an error
        if self.search_names:
            self.search_move()
        else:
            self.vimiv.statusbar.err_message("No matching file")

    def search_move(self, index=0, forward=True):
        """ Move to the next/previous search """
        # Correct handling of index
        if self.vimiv.keyhandler.num_str:
            index = int(self.vimiv.keyhandler.num_str)
            self.vimiv.keyhandler.num_str = ""
        if forward:
            self.search_pos += index
        else:
            self.search_pos -= index
        self.search_pos = self.search_pos % len(self.search_names)

        # Select file depending on library
        if self.vimiv.library.toggled:
            if len(self.search_names) == 1:
                self.vimiv.library.file_select("alt",
                                               self.search_names
                                                   [self.search_pos],
                                               "b",
                                               False)
            else:
                path = self.search_positions[self.search_pos]
                self.vimiv.library.treeview.set_cursor(Gtk.TreePath(path),
                                                         None, False)
                self.vimiv.library.treepos = path
        else:
            self.vimiv.keyhandler.num_str = str(self.search_positions[self.search_pos]+1)
            self.vimiv.image.move_pos()

    def reset_search(self):
        """ Simply resets all search parameters to null """
        self.search_names = []
        self.search_positions = []
        self.search_pos = 0
        return
