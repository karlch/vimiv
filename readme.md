![vimiv banner](https://raw.githubusercontent.com/karlch/vimiv/master/icons/vimiv_banner_400.png)

[![License badge](https://img.shields.io/aur/license/vimiv.svg)](https://raw.githubusercontent.com/karlch/vimiv/master/LICENSE)
[![codecov](https://codecov.io/gh/karlch/vimiv/branch/master/graph/badge.svg)](https://codecov.io/gh/karlch/vimiv)
[![Version badge](https://img.shields.io/aur/version/vimiv.svg)](https://aur.archlinux.org/packages/vimiv/)

#### Version 0.6.1 (unreleased)

[Releases](https://github.com/karlch/vimiv/releases "releases")
|
[Changelog](https://github.com/karlch/vimiv/blob/master/changelog.md "changelog")

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

#### Open image and library

![image + library](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-lib.png)

#### Thumbnail mode

![thumbnail mode](https://raw.githubusercontent.com/karlch/vimiv/gh-pages/vimiv-thumb.png)

## Configuration
Vimiv comes with two configuration files. The vimivrc for general settings and
the keys.conf for all keybindings. See vimivrc(5) for further information.

## Dependencies
* python3
* python-gobject
* gtk3
* python-pillow
* python-setuptools (for installation)
* imagemagick (optional for the optimization of images)
* jhead (optional for much better autorotation depending on EXIF data)

## Installation
Be sure to install the dependencies first. A simple `sudo make install` should
then suffice. For arch-users there is an AUR package called vimiv for the latest
stable version and vimiv-git for the developing branch.

To remove vimiv the standard `sudo make uninstall` works.

## Documentation
Vimiv comes with two man-pages for further documentation: vimiv(1) for general
information and vimivrc(5) for the configuration files.

## Thanks to
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.
