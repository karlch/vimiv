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

### Fedora Linux

For Fedora, [stable releases of vimiv][https://src.fedoraproject.org/rpms/vimiv] can be
installed from the official repositories using DNF or using Gnome Software:
```
# sudo dnf install vimiv
```

### Dependencies

* python3
* python-gobject
* gtk3
* python-setuptools for installation
* on debian-based systems: python-dev for installation
* optional: libgexiv2 for exif support
