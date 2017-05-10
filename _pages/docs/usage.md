---
layout: page
title: Usage
permalink: /docs/usage
---

#### Getting started

You can start vimiv from any application launcher with its .desktop file or
from the command line using the `vimiv` command. If any valid image paths are
given, the images are opened directly, otherwise the library is opened.

To close vimiv press `q`, `^q (Control+q)` or type in `:q` in the command line.

Vimiv is, as one would expect from an application with vim-like keybindings,
completely keyboard driven. To get you started some of the most important
keybindings for controlling vimiv are listed below. For a complete list of
them check out the [keybindings]({{ site.baseurl
}}/docs/keybindings-commands#keybindings) documentation.

#### Image

Scrolling the image is done with `hjkl`. The next image is selected with `n`,
the previous one with `p`. To show the first/last image use `g/G`.

Zooming in and out is done with `+/-`. To fit the image to the current window
size use `w`. `e/E` fit horizontally/vertically.

#### Library

The behaviour of the library is similar to the one of the file manager
[ranger](http://ranger.nongnu.org/). You can scroll down/up with `j/k`. `g/G`
select the first/last file in the list. `h` opens the parent directory while
`l` selects the current file. If the file is a directory, it is opened in the
library. An image is displayed to the right of the library. Pressing `l` again
closes the library and focuses the image.

Toggle the library with `o`, toggle focus between the library and the last
other widget with `O (Shift+o)`.

#### Thumbnail

Thumbnail mode is toggled with `t`. As always `hjkl` and `g/G` work as
expected.

It is also possible to vary the size of the thumbnails with the `+/-` keys.

#### Image editing

Images can be rotated with the `<` and `>`, flipped with the `|` and `_` keys.
These changes are automatically applied to the file. An image is deleted with
`x`. This actually moves the image to the trash directory specified by the
freedesktop standard, by default <b class="filename">$XDG_DATA_HOME/Trash</b>.

For additional editing open manipulate mode with `c`. Here brightness, contrast
and sharpness can be edited. To focus the respective slider use the `bcs` keys.
To apply the changes accept with `Return`, to leave manipulate mode reverting
any changes press `Escape`.

#### Command line

Similar to many keyboard centric programs, vimiv includes a simple commmand
line to run commands. It is opened with `:` and closed with `Return` to run a
command and `Escape` to discard it.

When entering the command line a completion window for vimiv's commands is
displayed. Pressing `Tab` completes to the best match if there is one,
continuing to press `Tab` cycles through the completions.

Entering `~`, `./`, or `/` at the beginning of the command line lets vimiv
interpret the command as a path. A valid directory/image is opened in the
library/image. Completing paths is also supported.

Prepending a command with `!` lets vimiv interpret the command as an external
command. The following text is passed to the shell. Here `%` is replaced with
the currently selected file and `*` with the current file list.  
  Example: `:!gimp %` 
  opens the currently selected image in gimp.

External commands can be "piped to vimiv" by appending the `|`
char to the command. The output of the command is then parsed by vimiv. If
the first line out output is a directory, it is opened in the library. If it
is a valid image, all lines are checked for images and these are opened.
Otherwise vimiv will try to run an internal command from the output.  
  Example: `:!find ~/Images -ctime -5 -type f |` 
  opens all files in ~/Images younger than five days.

To search through open files open the command line with `/`. Per default this
searches through the names incrementally and case-sensitively but this can be
changed in the configuration file.

Command line history is saved to
<b class="filename">$XDG_DATA_HOME/vimiv/history</b>.
History can be navigated and searched through using the `^P/^N` and `Up/Down`
keys.

Some commands support passing a [count] as repeat or step. If so, prepend
[count] to the command, e.g. `:5next`.

#### Marks and tags

Images are marked with `m`. To remove the mark from a marked image simply press
`m` again. `M` will toggle the mark status: If any images are marked, the marks
are cleared, otherwise the last list of marked images is marked again. To
quickly mark a bunch of images the `:mark_between` command is useful. It marks
all images between the last two marked images.

If images are marked, the simple manipulations (rotating, flipping and
deleting) are executed for all marked images and not for the current image.  In
thumbnail mode those actions will always apply to marked images. To save a list
of marked images, vimiv has a simple tag system.

`:tag_write tagname` saves the list of currently marked images to a file saved
in <b class="filename">$XDG_DATA_HOME/vimiv/Tags/tagname</b>.
If the file doesn't exist, it will be created. If it does, the names will
be appended to it, if they aren't in the tagfile already.  
`:tag_load tagname` loads all images in the tagfile tagname.  
`:tag_remove tagname` deletes the tagfile tagname.

#### More information

You may want to check out how to
[configure]({{ site.baseurl }}/docs/configuration) vimiv, a list of
all [keybindings]({{ site.baseurl }}/docs/keybindings-commands#keybindings)
or of all [commands]({{ site.baseurl }}/docs/keybindings-commands#commands).
