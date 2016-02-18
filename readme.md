### vimiv, an image viewer with vim-like keybindings

## Version 0.5

## Features
* vim-like keybindings
* thumbnail mode (supports caching of thumbnails)
* simple library browser (browse through folders and open images)
* basic image editing (rotate, flip, brightness, contrast and optimize)
* search directory recursively for images
* slideshow mode
* marking of images
* simple tag system
* searching with search highlight
* command line with tab-completion
* run external commands
* pipe external commands to vimiv

## Screenshots

**Open image and library:**

![Image](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-lib.jpg "Open image and library")

**Thumbnail mode:**

![Image](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-thumb.jpg "Thumbnail mode")

## Configuration
Vimiv comes with two configuration files. The vimivrc for general settings and
the keys.conf for all keybindings. See vimivrc(5) for further information.

The old configuration file vimivrc.py used in versions up to 0.4 is now
deprecated and can be deleted.

## Dependencies
* python3
* python-gobject
* gtk3
* python-pillow
* imagemagick (optional for the optimization of images)
* jhead (optional for much better autorotation depending on EXIF data)

## Installation
Be sure to install the dependencies first. A simple `sudo make (install)` should
then suffice. For arch-users there is an AUR package called vimiv-git.

To remove vimiv the standard `sudo make uninstall` works.

## Documentation
Vimiv comes with two man-pages for further documentation: vimiv(1) for general
information and vimivrc(5) for the configuration files.

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.

## License
In accordance with Pim vimiv is released under the MIT license.
