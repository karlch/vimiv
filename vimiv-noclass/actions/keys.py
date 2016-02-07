#!/usr/bin/env python
# encoding: utf-8
""" Handles key_press in vimiv """
from gi.repository import Gdk


def handle_key_press(widget, event, window, vimiv):
    """ Checks which key was pressed and activates the correct function """
    keyval = event.keyval
    keyname = Gdk.keyval_name(keyval)

    # Keys that don't support shift natively
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

    print(window)
    print(keyname)
    return
    # try:  # Numbers for the num_str
    #     if window == "COMMAND":
    #         raise ValueError
    #     int(keyname)
    #     self.num_append(keyname)
    #     return True
    # except:
    #     try:
    #         # Get the relevant keybindings for the window from the various
    #         # sections in the keys.conf file
    #         keys = self.keys[window]
    #         if window in ["IMAGE", "THUMBNAIL", "LIBRARY"]:
    #             keys.update(self.keys["GENERAL"])
    #         if window in ["IMAGE", "THUMBNAIL"]:
    #             keys.update(self.keys["IM_THUMB"])
    #         if window in ["IMAGE", "LIBRARY"]:
    #             keys.update(self.keys["IM_LIB"])
    #
    #         # Get the command to which the pressed key is bound
    #         func = keys[keyname]
    #         if "set " in func:
    #             conf_args = []
    #         else:
    #             func = func.split()
    #             conf_args = func[1:]
    #             func = func[0]
    #         # From functions dictionary get the actual vimiv command
    #         func = self.functions[func]
    #         args = func[1:]
    #         args.extend(conf_args)
    #         func = func[0]
    #         func(*args)
    #         return True  # Deactivates default bindings
    #     except:
    #         return False
