Keybindings are defined in the <b class="filename">keys.conf</b> file. Similar
to the vimivrc, this file is split up into sections:

* IMAGE: Keybindings defined here apply in image mode.
* THUMBNAIL: Keybindings defined here apply in thumbnail mode.
* LIBRARY: Keybindings defined here apply in library mode.
* MANIPULATE: Keybindings defined here apply in manipulate mode.
* COMMAND: Keybindings defined here apply in the command line.

Keybindings are defined in the form of:

<t class="command"><b>keyname</b>: <i>command [arguments]</i></t>

<b class="command">keyname</b> has to be a valid key symbol like "a" or "b", but
also e.g. "colon" for ":". A useful tool in X to check for these names
interactively is `xev`.

Supported modifiers are:

* Shift via Shift+keyname
* Control via ^keyname
* Alt via Alt+keyname

<i class="command">command [arguments]</i> has to be a valid vimiv
command with correct arguments. For a complete list of commands with
explanations check
<a href="{{ site.baseurl }}/docs/keybindings-commands#commands">the commands
documentation</a>.

Mouse bindings are defined in the same form. Simply use "Button" and the
corresponding number like "Button1" as keyname.
