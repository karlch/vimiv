### Vimiv, an image viewer with vim-like keybindings

## Version 0.1

## Features
* vim-like keybindings
* thumbnail mode (supports caching of thumbnails)
* simple library browser (browse through folders and open images)
* basic image editing (rotate, flip, brightness, contrast and optimize)
* search directory recursively for images
* slideshow mode

## Configuration
All options and keybindings can be configured in the file
`/etc/vimiv/vimivrc.py`. You can copy the file to `~/.vimiv/vimivrc.py` and
modify that file instead (recommended).

## Dependencies
* python3
* python-gobject
* gtk3
* python-pillow
* imagemagick (optional for the optimization of images)

## Installation
Be sure to install the dependencies first. A simple `sudo make` should then
suffice.

## Documentation
Vimiv comes with a man-page for further documentation.

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which Vimiv is
built.

Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.

## License
In accordance with Pim Vimiv is released under the MIT license.
