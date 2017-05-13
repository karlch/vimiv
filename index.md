---
layout: titlepage
---

Vimiv is an image viewer with vim-like keybindings. It is written in
python3 using the Gtk3 toolkit. Some of the features are:

* Thumbnail mode
* Simple library browser
* Basic image editing
* Command line with tab completion

For much more information please check out the [documentation](documentation).
If you are new to vimiv, this is a good place to
<a href="docs/usage#getting_started">get started</a>. For a
quick overview check out the
<a href="docs/keybindings_commands#keybinding-cheatsheet">
keybinding cheatsheet</a>.

<img src="{{ site.baseurl }}/images/screenshots/library.png" alt="Library">

### Downloads
See the GitHub
[releases](https://github.com/karlch/vimiv/releases)
page for available downloads. Check the
[installation guide](docs/install)
for instructions on how to get vimiv running.

### Contributing and bugs

If you want to contribute, awesome! The
<a href="docs/develop#contributing">contribution guidelines</a>
will help to get you started.

For bugs and feature requests the best place to go is the
[issues](https://github.com/karlch/vimiv/issues) page on GitHub. You can also
contact me directly via email at
[karlch@protonmail.com](mailto:karlch@protonmail.com) if you prefer to do so.
If possible, please reproduce the bug running with `--debug` and include the
content of the created logfile
in <t class="filename">$XDG_DATA_HOME/vimiv/vimiv.log</t>.

Vimiv tries to maintain backward compatibility with the latest Ubuntu
LTS version. Supporting older systems is not planned and things will
almost certainly break on them.


### Thanks to

* James Campos, author of [Pim](https://github.com/Narrat/Pim) which was the
  starting point for vimiv
* Bert Muennich, author of [Sxiv](https://github.com/muennich/sxiv) which
  inspired many of vimiv's features
* Anyone who has contributed or reported bugs
