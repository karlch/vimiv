---
layout: page
title: Installation
permalink: /docs/install
---

### General

Install the dependencies listed below first. To use the
development version clone the
[github repository](https://github.com/karlch/vimiv),
for the latest stable check out the 
[releases](https://github.com/karlch/vimiv/releases)
page. To install a simple
```
# make install
```
should suffice. To remove vimiv the standard
```
# make uninstall
```
works. You may need to update your icon cache after installation.

### Arch Linux

For Arch Linux users there are two packages in the AUR.
[vimiv](https://aur.archlinux.org/packages/vimiv/) for the
stable version and
[vimiv-git](https://aur.archlinux.org/packages/vimiv-git/)
for the development branch.

### Dependencies

* python3
* python-gobject
* Gtk3
* python-pillow
* python-setuptools for installation
* optional: jhead for better autorotation with exif data
