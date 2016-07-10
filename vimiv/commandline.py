#!/usr/bin/env python
# encoding: utf-8
""" Contains the commandline class for vimiv """
import re
import os
from threading import Thread
from subprocess import Popen, PIPE
from gi.repository import GLib, Gtk
from vimiv.fileactions import populate

# Directories
vimivdir = os.path.join(os.path.expanduser("~"), ".vimiv")
tagdir = os.path.join(vimivdir, "Tags")

class CommandLine(object):
    """ Commandline of vimiv """

    def __init__(self, vimiv):
        self.vimiv = vimiv

    def cmd_handler(self, entry):
        """ Handles input from the entry, namely if it is a path to be focused
        or a (external) command to be run """
        # cmd from input
        command = entry.get_text()
        # And close the cmd line
        self.vimiv.cmd_line_leave()
        if command[0] == "/":  # Search
            self.vimiv.search(command.lstrip("/"))
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
                self.vimiv.num_str = ""  # Be able to repeat commands
                while True:
                    try:
                        num = int(cmd[0])
                        self.vimiv.num_str = self.vimiv.num_str + str(num)
                        cmd = cmd[1:]
                    except:
                        break
                self.run_command(cmd)
        # Save the cmd to a list
        if command in self.vimiv.cmd_history:
            self.vimiv.cmd_history.remove(command)
        self.vimiv.cmd_history.insert(0, command)
        self.vimiv.cmd_pos = 0

    def run_external_command(self, cmd):
        """ Run the entered command in the terminal """
        # Check on which file(s) % and * should operate
        if self.vimiv.last_focused == "lib" and self.vimiv.files:
            filelist = self.vimiv.files
            fil = self.vimiv.files[self.vimiv.treepos]
        elif self.vimiv.paths:
            filelist = self.vimiv.paths
            fil = self.vimiv.paths[self.vimiv.index]
        else:
            filelist = []
            fil = ""
        if self.vimiv.marked:  # Always operate on marked files if they exist
            filelist = self.vimiv.marked
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
        dir = os.path.abspath(".")
        cmd_thread = Thread(target=self.thread_for_external, args=(cmd, dir))
        cmd_thread.start()
        # Undo the escaping
        fil = fil.replace("\\\\\\\\ ", " ")
        for i, f in enumerate(filelist):
            filelist[i] = f.replace("\\\\\\\\ ", " ")

    def thread_for_external(self, cmd, dir):
        """ Starting a new thread for external commands """
        try:
            # Possibility to "pipe to vimiv"
            if cmd[-1] == "|":
                cmd = cmd.rstrip("|")
                p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
                pipe = True
            else:
                p = Popen(cmd, stderr=PIPE, shell=True)
                pipe = False
            # Get output and error and run the command
            out, err = p.communicate()
            if p.returncode:
                err = err.decode('utf-8').split("\n")[0]
                self.vimiv.err_message(err)
            else:
                GLib.timeout_add(1, self.vimiv.reload_changes, dir, True, pipe, out)
            # Reload everything after an external command if we haven't moved,
            # you never know what happend ...
            # Must be in a timer because not all Gtk stuff can be accessed from
            # an external thread
        except FileNotFoundError as e:
            e = str(e)
            cmd = e.split()[-1]
            self.vimiv.err_message("Command %s not found" % (cmd))

    def pipe(self, input):
        """ Run output of external command in a pipe
            This checks for directories, files and vimiv commands """
        # Leave if no input came
        if not input:
            self.vimiv.err_message("No input from pipe")
            return
        # Make the input a file
        input = input.decode('utf-8')
        input = input.split("\n")[:-1]  # List of commands without empty line
        startout = input[0]
        # Do different stuff depending on the first line of input
        if os.path.isdir(startout):
            self.vimiv.move_up(startout)
        elif os.path.isfile(startout):
            # Remember oldfile if no image was in filelist
            if self.vimiv.paths:
                old_pos = [self.vimiv.paths[self.vimiv.index]]
                self.vimiv.paths = []
            else:
                old_pos = []
            # Populate filelist
            self.vimiv.paths, self.vimiv.index = populate(input)
            if self.vimiv.paths:  # Images were found
                self.vimiv.scrolled_win.show()
                self.vimiv.move_index(False, False, 0)
                # Close library if necessary
                if self.vimiv.library_toggled:
                    self.vimiv.toggle_library()
            elif old_pos:  # Nothing found, go back
                self.vimiv.paths, self.vimiv.index = populate(old_pos)
                self.vimiv.err_message("No image found")
        else:
            # Run every line as an internal command
            for cmd in input:
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
                self.vimiv.move_up(path)
                # If we open the library it must be focused as well
                self.vimiv.last_focused = "lib"
            else:
                # If it is an image open it
                self.vimiv.paths = []
                self.vimiv.paths, index = populate([path])
                self.vimiv.index = 0
                self.vimiv.move_index(True, False, index)
                #  Reload library in lib mode, do not open it in image mode
                abspath = os.path.dirname(path)
                if self.vimiv.last_focused == "lib":
                    self.vimiv.last_selected = path
                    self.vimiv.move_up(abspath)
                    # Focus it in the treeview so it can be accessed via "l"
                    for i, fil in enumerate(self.vimiv.files):
                        if fil in path:
                            self.vimiv.treeview.set_cursor(Gtk.TreePath(i),
                                                     None, False)
                            self.vimiv.treepos = i
                            break
                    # Show the image
                    self.vimiv.grid.set_size_request(self.vimiv.library_width-
                                               self.vimiv.border_width, 10)
                    self.vimiv.scrolled_win.show()
                else:
                    self.vimiv.move_up(abspath, True)
        except:
            self.vimiv.err_message("Warning: Not a valid path")

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
                self.vimiv.err_message(str(e))
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
            self.vimiv.err_message("No such command: %s" % (cmd))
