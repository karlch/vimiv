### Vimiv, an image viewer with vim-like keybindings

## Version 0.0.1

## Features
* vim-like keybindings
* thumbnail mode
* basic image editing (rotate, flip, brightness, contrast and optimize)

## Configuration
All options and keybindings can be configured in the file `/etc/vimivrc.py`. You
can copy the file to `~/.vimiv/vimivrc.py` and modify that file instead
(recommended).

## Dependencies
* python3
* pygobject
* python-pillow
* imagemagick (for the optimization)

## Installation
Be sure to install the dependencies first. A simple `sudo make` should then
suffice.

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

## License
In accordance with Pim Vimiv is released under the MIT license.
