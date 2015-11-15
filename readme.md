### Vimiv, an image viewer with vim-like keybindings

## Version 0.0.1

## Features
* vim-like keybindings
* thumbnail mode
* simple library browser (browse through folders and open images)
* basic image editing (rotate, flip, brightness, contrast and optimize)

## Configuration
All options and keybindings can be configured in the file `/etc/vimivrc.py`. You
can copy the file to `~/.vimiv/vimivrc.py` and modify that file instead
(recommended).

## Dependencies
* python3
* pygobject
* gtk3
* python-pillow
* imagemagick (for the optimization)

## Installation
Be sure to install the dependencies first. A simple `sudo make` should then
suffice.

## GTK3 recommendation
I recommend binding the following keys in `$theme/gtk/gtk-3.0/gtk-keys.css`:

    @binding-set gtk-vi-tree-view
    {
        bind "j" { "move-cursor" (display-lines, 1) };
        bind "k" { "move-cursor" (display-lines, -1) }
        bind "l" { "move-cursor" (logical-positions, 1) };
        bind "h" { "move-cursor" (logical-positions, -1) };
    }

    GtkTreeView {
    gtk-key-bindings: gtk-vi-tree-view;
    }

    GtkIconView {
        gtk-key-bindings: gtk-vi-tree-view
    }

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

## License
In accordance with Pim Vimiv is released under the MIT license.
