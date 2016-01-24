### vimiv, an image viewer with vim-like keybindings

## Version 0.4

## Features
* vim-like keybindings
* thumbnail mode (supports caching of thumbnails)
* simple library browser (browse through folders and open images)
* basic image editing (rotate, flip, brightness, contrast and optimize)
* search directory recursively for images
* slideshow mode
* marking of images
* simple tag system
* command line with tab-completion
* run external commands
* pipe external commands to vimiv

## Screenshots

**Open image and library:**

![Image](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-lib.jpg "Open image and library")

**Thumbnail mode:**

![Image](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-thumb.jpg "Thumbnail mode")

## Configuration
All options and keybindings can be configured in the file
`/etc/vimiv/vimivrc.py`. You can copy the file to `~/.vimiv/vimivrc.py` and
modify that file instead (recommended).

## Dependencies
* python3.5
* python-gobject
* gtk3
* python-pillow
* imagemagick (optional for the optimization of images)
* jhead (optional for much better autorotation depending on EXIF data)

## Installation
Be sure to install the dependencies first. A simple `sudo make` should then
suffice. For arch-users there is an AUR package called vimiv-git.

## Documentation
Vimiv comes with a man-page for further documentation.

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.

## License
In accordance with Pim vimiv is released under the MIT license.
