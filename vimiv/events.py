#!/usr/bin/env python
# encoding: utf-8
"""Handle events for vimiv, e.g. fullscreen, resize, keypress."""

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from vimiv.helpers import scrolltypes
from vimiv.parser import parse_keys


class Window(object):
    """Window class for vimiv which handles fullscreen and resize."""

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        self.vimiv = vimiv
        self.fullscreen = False
        if Gtk.get_minor_version() > 10:
            self.vimiv.connect_data('window-state-event',
                                    Window.on_window_state_change,
                                    self)
        else:
            self.vimiv.connect_object('window-state-event',
                                      Window.on_window_state_change,
                                      self)
        self.last_focused = ""

        # The configurations from vimivrc
        general = settings["GENERAL"]

        # General
        start_fullscreen = general["start_fullscreen"]
        if start_fullscreen:
            self.toggle_fullscreen()

        # Connect
        self.vimiv.connect("check-resize", self.auto_resize)
        for widget in [self.vimiv.library.treeview,
                       self.vimiv.thumbnail.iconview,
                       self.vimiv.manipulate.scale_bri,
                       self.vimiv.manipulate.scale_con,
                       self.vimiv.manipulate.scale_sha,
                       self.vimiv.image.image]:
            widget.connect("button-release-event", self.focus_on_mouse_click)

    def on_window_state_change(self, event, window=None):
        """Handle fullscreen/unfullscreen correctly.

        Args:
            event: Gtk event that called the function.
            window: Gtk.Window to operate on.
        """
        if window:
            window.fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                     & event.new_window_state)
        else:
            self.fullscreen = bool(Gdk.WindowState.FULLSCREEN
                                   & event.new_window_state)

    def toggle_fullscreen(self):
        """Toggle fullscreen."""
        if self.fullscreen:
            self.vimiv.unfullscreen()
        else:
            self.vimiv.fullscreen()

    def auto_resize(self, window):
        """Automatically resize widgets when window is resized.

        Args: window: The window which emitted the resize event.
        """
        if self.vimiv.get_size() != self.vimiv.winsize:
            self.vimiv.winsize = self.vimiv.get_size()
            if self.vimiv.paths:
                if self.vimiv.thumbnail.toggled:
                    self.vimiv.thumbnail.calculate_columns()
                if not self.vimiv.image.user_zoomed:
                    self.vimiv.image.zoom_to(0)
            self.vimiv.commandline.info.set_max_width_chars(
                self.vimiv.winsize[0] / 16)

    def focus_on_mouse_click(self, widget, event_button):
        """Update statusbar with the currently focused widget after mouse click.

        Args:
            widget: The widget that emitted the signal.
            event_button: Mouse button that was pressed.
        """
        self.vimiv.statusbar.update_info()


class KeyHandler(object):
    """Handle key press for vimiv invoking the correct commands.

    Attributes:
        vimiv: The main vimiv class to interact with.
        num_str: String containing repetition number for commands.
        keys: Keybindings from configfiles.
    """

    def __init__(self, vimiv, settings):
        """Create the necessary objects and settings.

        Args:
            vimiv: The main vimiv class to interact with.
            settings: Settings from configfiles to use.
        """
        # Add events to vimiv
        self.vimiv = vimiv
        self.vimiv.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                              Gdk.EventMask.POINTER_MOTION_MASK)
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
                func = self.vimiv.functions[func]
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
        if self.vimiv.thumbnail.toggled:
            self.vimiv.thumbnail.move_direction(direction)
        else:
            self.vimiv.image.scrolled_win.emit('scroll-child',
                                               scrolltypes[direction][0],
                                               scrolltypes[direction][1])
        return True  # Deactivates default bindings (here for Arrows)

    def num_append(self, num):
        """Add a new char to num_str."""
        self.num_str += num
        # RISKY
        GLib.timeout_add_seconds(1, self.num_clear)
        self.vimiv.statusbar.update_info()

    def num_clear(self):
        """Clear num_str."""
        self.num_str = ""
        self.vimiv.statusbar.update_info()
