#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Handles the keyboard for vimiv."""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib
from vimiv.configparser import parse_keys


class KeyHandler(object):
    """Handle key press for vimiv invoking the correct commands.

    Attributes:
        app: The main vimiv application to interact with.
        num_str: String containing repetition number for commands.
        timer_id: ID of the current timer running to clear num_str.
        keys: Keybindings from configfiles.
    """

    def __init__(self, app, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        # Add events to vimiv
        self.app = app
        # Settings
        self.num_str = ""
        self.timer_id = 0
        self.keys = parse_keys()

    def run(self, widget, event, window):
        """Run the correct function per keypress.

        Args:
            widget: Focused Gtk Object.
            event: KeyPressEvent that called the function.
            window: Gtk.Window to operate on.
        """
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        shiftkeys = ["space", "Return", "Tab", "Escape", "BackSpace",
                     "Up", "Down", "Left", "Right"]
        # Check for Control (^), Mod1 (Alt) or Shift
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            keyname = "^" + keyname
        if event.get_state() & Gdk.ModifierType.MOD1_MASK:
            keyname = "Alt+" + keyname
        # Shift+ for all letters and for keys that don't support it
        if (event.get_state() & Gdk.ModifierType.SHIFT_MASK and
                (len(keyname) < 2 or keyname in shiftkeys)):
            keyname = "Shift+" + keyname.lower()
        if keyname == "ISO_Left_Tab":  # Tab is named really weird under shift
            keyname = "Shift+Tab"
        # Numbers for the num_str
        if window != "COMMAND" and keyname.isdigit():
            self.num_append(keyname)
            return True
        # Get the relevant keybindings for the window from the various
        # sections in the keys.conf file
        keys = self.keys[window]
        # Get the command to which the pressed key is bound and run it
        if keyname in keys:
            keybinding = keys[keyname]
            # Write keybinding and key to log in debug mode
            if self.app.debug:
                self.app["log"].write_message("key",
                                              keyname + ": " + keybinding)
            self.app["commandline"].run_command(keybinding, keyname)
            return True  # Deactivates default bindings
        # Activate default keybindings
        else:
            return False

    def num_append(self, num, remove_by_timeout=True):
        """Add a new char to num_str.

        Args:
            num: The number to append to the string.
            remove_by_timeout: If True, add a timeout to clear the num_str.
        """
        # Remove old timers if we have new numbers
        if self.timer_id:
            GLib.source_remove(self.timer_id)
        self.timer_id = GLib.timeout_add_seconds(1, self.num_clear)
        self.num_str += num
        # Write number to log file in debug mode
        if self.app.debug:
            self.app["log"].write_message("number", num + "->" + self.num_str)
        self.app["statusbar"].update_info()

    def num_clear(self):
        """Clear num_str."""
        # Remove any timers as we are clearing now anyway
        if self.timer_id:
            GLib.source_remove(self.timer_id)
        # Write number cleared to log file in debug mode
        if self.app.debug and self.num_str:
            self.app["log"].write_message("number", "cleared")
        self.timer_id = 0
        # Reset
        self.num_str = ""
        self.app["statusbar"].update_info()
