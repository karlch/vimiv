#!/usr/bin/env python
# encoding: utf-8
"""Handles the keyboard for vimiv."""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib
from vimiv.helpers import scrolltypes
from vimiv.parser import parse_keys


class KeyHandler(object):
    """Handle key press for vimiv invoking the correct commands.

    Attributes:
        app: The main vimiv application to interact with.
        num_str: String containing repetition number for commands.
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
        try:  # Numbers for the num_str
            if window == "COMMAND":
                raise ValueError
            int(keyname)
            self.num_append(keyname)
            return True
        except:
            try:
                # Get the relevant keybindings for the window from the various
                # sections in the keys.conf file
                keys = self.keys[window]

                # Get the command to which the pressed key is bound
                func = keys[keyname]
                if "set " in func:
                    conf_args = []
                else:
                    func = func.split()
                    conf_args = func[1:]
                    func = func[0]
                # From functions dictionary get the actual vimiv command
                func = self.app.functions[func]
                args = func[1:]
                args.extend(conf_args)
                func = func[0]
                func(*args)
                return True  # Deactivates default bindings
            except:
                return False

    def scroll(self, direction):
        """Scroll the correct object.

        Args:
            direction: Scroll direction to emit.
        """
        if self.app["thumbnail"].toggled:
            self.app["thumbnail"].move_direction(direction)
        else:
            self.app["image"].scrolled_win.emit('scroll-child',
                                                scrolltypes[direction][0],
                                                scrolltypes[direction][1])
        return True  # Deactivates default bindings (here for Arrows)

    def num_append(self, num):
        """Add a new char to num_str."""
        self.num_str += num
        # RISKY
        GLib.timeout_add_seconds(1, self.num_clear)
        self.app["statusbar"].update_info()

    def num_clear(self):
        """Clear num_str."""
        self.num_str = ""
        self.app["statusbar"].update_info()
