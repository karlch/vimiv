### Vimiv, an image viewer with vim-like keybindings

## Version 0.1.0

## Features
* vim-like keybindings
* thumbnail mode (supports caching of thumbnails)
* simple library browser (browse through folders and open images)
* basic image editing (rotate, flip, brightness, contrast and optimize)
* search directory recursively for images
* slideshow mode

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

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which Vimiv is
built.
Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.

## License
In accordance with Pim Vimiv is released under the MIT license.
