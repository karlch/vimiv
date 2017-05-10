---
layout: page
permalink: /docs/keybindings-commands
---

# Keybindings

The default keybindings are in <b class="filename">/etc/vimiv/keys.conf</b>.
The keys are bound to commands. For a complete list of commands with
explanation read the [next section](#commands).

Entering a number anywhere but in the command line will save the number as
[count]. The current [count] is displayed in the statusbar at the bottom
right.  Some commands support passing [count] as repeat or step.

#### Keybinding Cheatsheet

<h6>
<a href="javascript:unhide('image_header')" class="unhidden_header" id="image_header">Image</a>
<a href="javascript:unhide('library_header')" class="hidden_header" id="library_header">Library</a>
<a href="javascript:unhide('thumbnail_header')" class="hidden_header" id="thumbnail_header">Thumbnail</a>
<a href="javascript:unhide('manipulate_header')" class="hidden_header" id="manipulate_header">Manipulate</a>
</h6>
<div id="toggle_image" class="unhidden">
    <center><a href="{{ site.baseurl }}/images/keybindings/keyboard_image.png"><img src="{{ site.baseurl }}/images/keybindings/keyboard_image.png"></a></center>
</div>
<div id="toggle_library" class="hidden">
    <center><a href="{{ site.baseurl }}/images/keybindings/keyboard_library.png"><img src="{{ site.baseurl }}/images/keybindings/keyboard_library.png"></a></center>
</div>
<div id="toggle_thumbnail" class="hidden">
    <center><a href="{{ site.baseurl }}/images/keybindings/keyboard_thumbnail.png"><img src="{{ site.baseurl }}/images/keybindings/keyboard_thumbnail.png"></a></center>
</div>
<div id="toggle_manipulate" class="hidden">
    <center><a href="{{ site.baseurl }}/images/keybindings/keyboard_manipulate.png"><img src="{{ site.baseurl }}/images/keybindings/keyboard_manipulate.png"></a></center>
</div>

# Commands

All vimiv keybindings are mapped to commands. Some of the commands are not
accessible from the command line as they are not useful to be run by hand.

#### Summary of commands

{% include_relative include/commands.md %}

#### Description of commands

{% include_relative include/commands_description.md %}

#### Summary of hidden commands

These commands can only be bound to keys and are not accessible from the command
line.

{% include_relative include/hidden_commands.md %}

#### Description of hidden commands

{% include_relative include/hidden_commands_description.md %}
