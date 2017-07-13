# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Handles the keyboard for vimiv."""

from gi.repository import Gdk, GLib, GObject
from vimiv.config_parser import parse_keys
from vimiv.helpers import get_float, get_int


class EventHandler(GObject.Object):
    """Handle keyboard/mouse/touch events for vimiv.

    Attributes:
        num_str: String containing repetition number for commands.

        _app: Main vimiv application to interact with.
        _keys: Keybindings from configfiles.
        _timer_id: ID of the current timer running to clear num_str.
        _timer_id_touch: ID of the current timer running to reconnect clicks
            after a touch by touchscreen.
    """

    def __init__(self, app):
        """Initialize defaults."""
        super(EventHandler, self).__init__()
        self._num_str = ""
        self._app = app
        self._timer_id = 0
        self._timer_id_touch = 0
        self._keys = parse_keys(running_tests=self._app.running_tests)

    def on_key_press(self, widget, event, widget_name):
        """Handle key press event."""
        if event.type == Gdk.EventType.KEY_PRESS:
            keyval = event.keyval
            keyname = Gdk.keyval_name(keyval)
        keyname = self._check_modifiers(event, keyname)
        return self._run(keyname, widget_name)

    def on_click(self, widget, event, widget_name):
        """Handle click event."""
        # Do not handle double clicks
        if not event.type == Gdk.EventType.BUTTON_PRESS:
            return
        button_name = "Button" + str(event.button)
        button_name = self._check_modifiers(event, button_name)
        return self._run(button_name, widget_name)

    def _run(self, keyname, widget_name):
        """Run the correct function per keypress.

        Args:
            keyname: Name of the key that was pressed/clicked/...
            widget_name: Name of widget to operate on: image, library...
        """
        # Numbers for the num_str
        if widget_name != "COMMAND" and keyname.isdigit():
            self.num_append(keyname)
            return True
        # Get the relevant keybindings for the window from the various
        # sections in the keys.conf file
        keys = self._keys[widget_name]
        # Get the command to which the pressed key is bound and run it
        if keyname in keys:
            keybinding = keys[keyname]
            # Write keybinding and key to log in debug mode
            if self._app.debug:
                self._app["log"].write_message("key",
                                               keyname + ": " + keybinding)
            self._app["commandline"].run_command(keybinding, keyname)
            return True  # Deactivates default bindings
        # Activate default keybindings
        else:
            return False

    def on_touch(self, widget, event):
        """Clear mouse connection when touching screen.

        This stops calling the ButtonX bindings when using the touch screen.
        Reasoning: We do not want to e.g. move to the next image when trying to
            zoom in.
        """
        try:
            self._app["window"].disconnect_by_func(self.on_click)
        # Was already disconnected
        except TypeError:
            pass
        if self._timer_id_touch:
            GLib.source_remove(self._timer_id_touch)
        self._timer_id_touch = GLib.timeout_add(5, self._reconnect_click)
        return True

    def _reconnect_click(self):
        """Reconnect the click signal after a touch event."""
        self._app["window"].connect("button_press_event",
                                    self.on_click, "IMAGE")
        self._timer_id_touch = 0

    def _check_modifiers(self, event, keyname):
        """Update keyname according to modifiers in event."""
        shiftkeys = ["space", "Return", "Tab", "Escape", "BackSpace",
                     "Up", "Down", "Left", "Right"]
        # Check for Control (^), Mod1 (Alt) or Shift
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            keyname = "^" + keyname
        if event.get_state() & Gdk.ModifierType.MOD1_MASK:
            keyname = "Alt+" + keyname
        # Shift+ for all letters and for keys that don't support it
        if (event.get_state() & Gdk.ModifierType.SHIFT_MASK and
                (len(keyname) < 2 or keyname in shiftkeys
                 or keyname.startswith("Button"))):
            keyname = "Shift+" + keyname.lower()
        if keyname == "ISO_Left_Tab":  # Tab is named really weird under shift
            keyname = "Shift+Tab"
        return keyname

    def num_append(self, num, remove_by_timeout=True):
        """Add a new char to num_str.

        Args:
            num: The number to append to the string.
            remove_by_timeout: If True, add a timeout to clear the num_str.
        """
        # Remove old timers if we have new numbers
        if self._timer_id:
            GLib.source_remove(self._timer_id)
        self._timer_id = GLib.timeout_add_seconds(1, self.num_clear)
        self._num_str += num
        self._convert_trailing_zeros()
        # Write number to log file in debug mode
        if self._app.debug:
            self._app["log"].write_message("number", num + "->" + self._num_str)
        self._app["statusbar"].update_info()

    def num_clear(self):
        """Clear num_str."""
        # Remove any timers as we are clearing now anyway
        if self._timer_id:
            GLib.source_remove(self._timer_id)
        # Write number cleared to log file in debug mode
        if self._app.debug and self._num_str:
            self._app["log"].write_message("number", "cleared")
        self._timer_id = 0
        # Reset
        self._num_str = ""
        self._app["statusbar"].update_info()

    def num_receive(self, number=1, to_float=False):
        """Receive self._num_str and clear it.

        Args:
            number: Number to return if self._num_str is empty.
            to_float: If True, convert num_str to float. Else to int.
        Return:
            The received number or default.
        """
        if self._num_str:
            number = get_float(self._num_str) \
                if to_float else get_int(self._num_str)
            self.num_clear()
        return number

    def get_num_str(self):
        return self._num_str

    def set_num_str(self, number):
        self.num_clear()
        self.num_append(str(number))

    def _convert_trailing_zeros(self):
        """If prefixed with zero add a decimal point to self._num_str."""
        if self._num_str.startswith("0") and not self._num_str.startswith("0."):
            self._num_str = self._num_str.replace("0", "0.")
