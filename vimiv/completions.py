#!/usr/bin/env python3
# encoding: utf-8
""" The command line completion for vimiv """

import os
import re
from vimiv.helpers import listdir_wrapper
from vimiv.helpers import external_commands
from vimiv.fileactions import is_image


class Completion():

    """ Class for the command line completion
        Different functions for the different completion types """

    def __init__(self, command, commandlist, repeat="", show_hidden=False):
        """ Requieres the entered command and a list of the possible
            completions; an integer which says how often the entered command
            shall be executed is optional and defaults to 0 (not used);
            boolean to show hidden files or not """
        self.command = command  # entered text
        self.completions = commandlist  # internal commands (default completion)
        self.repeat = repeat  # numstr for repetition
        self.show_hidden = show_hidden

    def complete(self):
        """ Finds out which type of completion should be done and executes the
            correct function """
        # Tab presses are remembered so one can tab through all the completions
        comp_type = "internal"
        # Generate list of possible completions depending on the type of
        # completion
        # Nothing entered -> checks are useless
        if self.command:
            # External commands are prefixed with an !
            if self.command[0] == "!":
                self.completions = self.complete_external()
                comp_type = "external"
            # Paths are prefixed with a /
            elif self.command[0] in ["/", ".", "~"]:
                self.completions = self.complete_path(self.command)
                comp_type = "path"
            # Tag commands
            elif re.match(r'^(tag_(write|remove|load) )', self.command):
                self.completions = self.complete_tag()
                comp_type = "tag"

        # Sort out the completions
        # Check if the entered text matches the beginning of a command
        completions = []
        matchstr = '^(' + self.command + ')'
        for item in self.completions:
            if re.match(matchstr, item):
                completions.append(item)

        # Find the best matching completion as output
        if completions:
            compstr, output = self.best_match(completions, comp_type)

        else:
            compstr = "  No matching completion"
            output = ":" + self.command

        # Return the best matching completion and the string with all
        # suggestions
        return output, compstr, completions

    def best_match(self, completions, comp_type):
        """ Finds the best matching completion and returns the formatted
            completions and the best match"""
        # Output, start with : and the prepended numbers
        output = ":" + self.repeat
        # Find last equal character
        first = completions[0]
        last = completions[-1]
        for i, char in enumerate(first):
            if char == last[i]:
                output += char
            else:
                break

        # Only show the filename if completing self.paths
        if comp_type == "path":
            for i, comp in enumerate(completions):
                if comp.endswith("/"):
                    completions[i] = comp.split("/")[-2] + "/"
                else:
                    completions[i] = os.path.basename(comp)
        # And only the tags if completing tags
        elif comp_type == "tag":
            for i, comp in enumerate(completions):
                completions[i] = " ".join(comp.split()[1:])

        # A string with possible completions for the info if here is more
        # than one completion
        if len(completions) > 1:
            compstr = "  ".join(completions)
        else:
            compstr = ""

        return compstr, output

    def complete_internal(self):
        pass

    def complete_tag(self):
        """ Appends the available tag names to an internal tag command """
        tags = listdir_wrapper(os.path.expanduser("~/.vimiv/Tags"),
                               self.show_hidden)
        completions = []
        for tag in tags:
            completions.append(self.command.split()[0] + " " + tag)
        return completions

    def complete_external(self):
        """ Completion of external commands """
        arguments = self.command.split()
        # Check if path completion would be useful
        # Assumed the case if we have more than one argument and the last one is
        # not an option
        if len(arguments) > 1 and arguments[-1][0] != "-":
            # Path to be completed is last argument
            path = arguments[-1]
            files = self.complete_path(path, True)
            # Command is everything ahead
            cmd = " ".join(arguments[:-1])
            # Join both for a commandlist
            commandlist = []
            for fil in files:
                commandlist.append(cmd + " " + fil)
            return sorted(commandlist)
        # If no path is necessary return a list of all external commands
        else:
            return external_commands

    def complete_path(self, path, external_command=False):
        """ Returns a nicely formated filelist inside path
            If not running within an external command it will sort out
            unsupported filetypes """
        # Directory of the path, default to .
        directory = os.path.dirname(path) if os.path.dirname(path) else path
        if not os.path.exists(os.path.expanduser(directory)):
            directory = "."
        # Files in that directory
        files = listdir_wrapper(directory, self.show_hidden)
        # Format them neatly depending on directory and type
        filelist = []
        for fil in files:
            if directory != "." or not external_command:
                fil = os.path.join(directory, fil)
            # Directory
            if os.path.isdir(os.path.expanduser(fil)):
                filelist.append(fil + "/")
            # Acceptable file
            elif is_image(fil) or external_command:
                filelist.append(fil)
        return filelist


class VimivComplete(object):
    """ Inherits from vimiv to communicate with the widget """

    def __init__(self, vimiv):
        self.vimiv = vimiv
        self.tab_presses = 0
        self.cycling = False
        self.completions = []
        self.completions_reordered = []
        self.output = ""
        self.compstr = ""

    def complete(self, inverse=False):
        """ Simple autocompletion for the command line """
        # Remember old completion
        previous_output = self.output
        if not self.cycling:
            command = self.vimiv.commandline.entry.get_text()
            command = command.lstrip(":")
            # Strip prepending numbers
            numstr = ""
            while True:
                try:
                    num = int(command[0])
                    numstr += str(num)
                    command = command[1:]
                except:
                    break
            # Generate completion class and get completions
            commandlist = sorted(list(self.vimiv.commands.keys()))
            completion = Completion(command, commandlist)
            self.output, self.compstr, self.completions = completion.complete()
            self.completions_reordered = self.completions

            # Set text
            self.vimiv.commandline.entry.set_text(self.output)
            self.vimiv.commandline.info.set_markup(self.compstr)
            self.vimiv.commandline.entry.set_position(-1)

        if len(self.completions) > 1:
            self.vimiv.commandline.info.show()

        # Cycle through completions on multiple tab
        if self.output == previous_output:
            if self.cycling:
                if inverse:
                    self.tab_presses -= 1
                else:
                    self.tab_presses += 1
            command_position = self.tab_presses % len(self.completions)
            command = self.completions[command_position]
            prepended = self.not_common(self.output, command)
            new_text = prepended + command
            # Remember tab_presses because changing text resets
            tab_presses = self.tab_presses
            self.vimiv.commandline.entry.set_text(new_text)
            self.tab_presses = tab_presses
            self.vimiv.commandline.entry.set_position(-1)
            # Get maximum and current pos to always show current completion
            line_length = self.vimiv.commandline.info.get_max_width_chars()*2
            cur_index = self.completions_reordered.index(command)
            cur_pos = len("  ".join(self.completions_reordered[0:cur_index+1]))
            # Rewrap if we are out of the displayable area
            if cur_pos > line_length:
                self.completions_reordered = self.completions[command_position:] + \
                                             self.completions[:command_position]
                cur_index = 0
            highlight = self.vimiv.library.markup + \
                        "<b>" + command + "</b></span>"
            completions = list(self.completions_reordered)  # Pythonic list copy
            completions[cur_index] = highlight
            compstr = "  ".join(completions)
            self.vimiv.commandline.info.set_markup(compstr)
            self.vimiv.commandline.info.show()
            self.cycling = True

        return True  # Deactivates default bindings (here for Tab)

    def reset(self):
        """ Simply empty completions """
        self.tab_presses = 0
        self.cycling = False
        self.completions = []
        self.compstr = ""
        self.vimiv.commandline.info.set_markup(self.compstr)

    def not_common(self, output, completion):
        """ Returns everything but the common match at the end of output """
        for i in range(len(completion)):
            end = len(completion) - i
            possible_ending = completion[:end]
            if output.endswith(possible_ending):
                return output.rstrip(possible_ending)
        return output
