---
layout: page
permalink: /docs/manpage
---

# VIMIV 1 "May 2017" Linux vimiv

## NAME
vimiv - an image viewer with vim-like keybindings

## SYNOPSIS
`vimiv`
[`-bBfFhlLrRsSv`]
[`--start-from-desktop`]
[`--slideshow`]
[`--slideshow-delay` *SLIDESHOW-DELAY*]
[`-g`, `--geometry` *GEOMETRY*]
[`--temp-basedir`]
[`--config` *FILE*]
[`--debug`]
[*FILE*]
...

## DESCRIPTION
Vimiv is an image viewer with vim-like keybindings. It is written in
python3 using the Gtk3 toolkit. Some of the features are:

* Thumbnail mode
* Simple library browser
* Basic image editing
* Command line with tab completion

The complete documentation is not included in this manpage but is available at:

http://karlch.github.io/vimiv/documentation

## OPTIONS
`-b`, `--bar`
  display the statusbar

`-f`, `--fullscreen`
  start in fullscreen

`-h`, `--help`
  display a simple help text

`-l`, `--library`
  display the library

`-r`, `--recursive`
  search the directory recursively for images

`-s`, `--shuffle`
  shuffle the filelist

`-v`, `--version`
  show version information and exit

`--start-from-desktop`
  start using the desktop\_start\_dir as path

`--slideshow`
  start in slideshow mode

`--slideshow-delay` *SLIDESHOW_DELAY*
  set the slideshow delay

`-g`, `--geometry` *GEOMETRY*
  set the starting geometry

`--temp-basedir`
  use a temporary basedir

`--config` *FILE*
  use FILE as local configuration file instead of
  $XDG\_CONFIG\_HOME/vimiv/vimivrc and ~/.vimiv/vimivrc.

`--debug`
  run in debug mode

All capitals negate the setting, so e.g. -B means do not display the statusbar.
For the long version prepend no-, e.g. --no-bar.

## BUGS
Probably. Please contact me under \<karlch at protonmail dot com\> or, even
better, open an issue on the github homepage.

## SEE ALSO
vimivrc(5)

## THANKS TO
James Campos, author of Pim https://github.com/Narrat/Pim upon which vimiv is
built.

Bert Muennich, author of sxiv https://github.com/muennich/sxiv which inspired
many of the features of vimiv.

Anyone who has contributed or reported bugs.

## RESOURCES
**Website**
https://karlch.github.io/vimiv/

**Github**
https://github.com/karlch/vimiv/
