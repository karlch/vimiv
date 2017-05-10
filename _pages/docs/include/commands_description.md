##### accept\_changes
Accept changes made in manipulate.

Refers to brightnes, contrast and sharpness of the image.

##### alias
**Syntax:** <t class="command"><b>:alias</b> <i>aliasname command</i></t>  
Add an alias for a command. Works for any type of command, including paths and
external commands.

**Example:** <t class="command"><b>:alias</b> <i>bkg !hsetroot %</i></t>  
Add an alias bkg to set the desktop background to the currently selected image.

**Positional arguments:**
* <i class="command">aliasname</i>: Name of the alias to add.
* <i class="command">command</i>: Command for which the alias is created.

##### autorotate
Rotate all images in the current filelist according to exif data.

If <code>jhead</code> is installed, it is used for its better performance.
Otherwise the python pillow module is used.

##### center
Scroll to the center of the current image.

##### copy\_abspath
Copy the absolute path of the currently selected file to the clipboard.

The selection is either clipboard or primary depending on the
[copy\_to\_primary]({{ site.baseurl
}}/docs/configuration#copy-to-primary) setting.

##### copy\_basename
Copy the base name of the currently selected file to the clipboard.

The selection is either clipboard or primary depending on the
[copy\_to\_primary]({{ site.baseurl
}}/docs/configuration#copy-to-primary) setting.

##### delete
Delete the currently selected image.

This moves the image to the trash directory specified by the freedesktop
standard, per default <b class="filename">$XDG_DATA_HOME/Trash/</b>.

##### discard\_changes
Discard any changes made in manipulate mode and leave it.

This resets brightness, contrast and sharpness to 0 and restores the original
image.

##### first
Move to the first image of the filelist in image/thumbnail mode.

**Count:** Move to the [count]th image instead.

##### first\_lib
Move to the first image of the filelist in the library.

**Count:** Move to the [count]th image instead.

##### fit
Fit the image to the current window size.

Essentially a convenience command doing the same as <t class="command">
<b>zoom_to</b> <i>0</i></t>. 

##### fit\_horiz
Fit the image horizontally to the current window size.

##### fit\_vert
Fit the image vertically to the current window size.

##### flip
**Syntax:** <t class="command"><b>:flip</b> <i>direction</i></t>

Flip the current image.

**Positional arguments:**
* <i class="command">direction</i>: Flip direction. 1 to flip horizontally, 0 to
  flip vertically.

##### focus\_library
Focus the library.

##### format
**Syntax:** <t class="command"><b>:format</b> <i>formatstring</i></t>

Format all currently open filenames.

Rename all currently open images in the form of
<i class="command">formatstring</i>001.ending,
<i class="command">formatstring</i>002.ending, and so on. If all currently open
images contain exif data, the formatstring can include "%Y", "%m", "%d", "%H",
"%M", and "%S". See `man 1 date` if you aren't sure what these mean.

**Positional arguments:**
* <i class="command">formatstring</i>: The string used to format the
  images.

##### fullscreen
Toggle fullscreen mode.

##### grow\_lib
**Syntax:** <t class="command"><b>:grow_lib</b> <i>[value]</i></t>

Increase the library width.

**Optional arguments:**
* <i class="command">value</i>: Value to increase width by. Defaults to 20.

**Count:** Multiply <i class="command">value</i> by [count].

##### last
Move to the last image of the filelist in image/thumbnail mode.

**Count:** Move to the [count]th image instead.

##### last\_lib
Move to the last image of the filelist in the library.

**Count:** Move to the [count]th image instead.

##### library
Toggle the library.

##### manipulate
Enter manipulate mode.

##### mark
Mark the currently selected image.

If the image is already marked, remove the mark.

##### mark\_all
Mark all images in the current filelist.

##### mark\_between
Mark all images between the last two marked images.

If any images are marked, the marks are cleared, otherwise the last list
of marked images is marked again.

##### mark\_toggle
Toggle the current mark status.

This clears all marked images if any are marked and otherwise restores the last
list of marked images.

##### move\_up
Move up one directory in the library.

The library is opened and focused if it is not open or focused yet.

**Count:** Move up [count] directories. So e.g. 2move\_up is equivalent to cd
../..

##### next
Move to the next image in the filelist of image mode.

**Count:** Move [count] images forward.

##### next!
Force moving to the next image in the filelist of image mode.

Discard any changes made in manipulate mode.

**Count:** Move [count] images forward.

##### prev
Move to the previous image in the filelist of image mode.

**Count:** Move [count] images backward.

##### prev!
Force moving to the previous image in the filelist of image mode.

Discard any changes made in manipulate mode.

**Count:** Move [count] images backward.

##### q
Quit vimiv.

Print any marked images to stdout.

##### q!
Force quitting vimiv.

Discard any changes made in manipulate mode. Print any marked images to stdout.

##### reload\_lib
Reload the library.

##### rotate
**Syntax:** <t class="command"><b>:rotate</b> <i>value</i></t>

Rotate the image counter-clockwise.

**Positional arguments:**
* <i class="command">value</i>: Rotate (<i class="command">value</i> % 4) times.

**Count:** Rotate the image ([count] * <i class="command">value</i> % 4) times.

##### set animation!
Toggle the animation status of animated Gifs.

##### set brightness
**Syntax:** <t class="command"><b>:set brightness</b> <i>[value]</i></t>

Set the brightness of the current image.

Enter manipulate mode if not there yet.

**Optional arguments:**
* <i class="command">value</i>: Value between -127 and 127 to set the brightness
  to. Defaults to 0.

##### set clipboard!
Toggle the [copy\_to\_primary]({{ site.baseurl
}}/docs/configuration#copy-to-primary) setting.

Switches between primary and clipboard.

##### set contrast
**Syntax:** <t class="command"><b>:set contrast</b> <i>[value]</i></t>

Set the contrast of the current image.

Enter manipulate mode if not there yet.

**Optional arguments:**
* <i class="command">value</i>: Value between -127 and 127 to set the contrast
  to. Defaults to 0.

##### set library\_width
**Syntax:** <t class="command"><b>:set library_width</b> <i>[value]</i></t>

Set the library width.

**Optional arguments:**
* <i class="command">value</i>: Value to set the library width to. Defaults to
  the [library\_width]({{
  site.baseurl}}/docs/configuration#library-width) setting.

##### set overzoom
**Syntax:** <t class="command"><b>:set overzoom</b> <i>[value]</i></t>

Set the [overzoom]({{
site.baseurl}}/docs/configuration#overzoom) setting.

**Optional arguments:**
* <i class="command">value</i>: Value to set the overzoom setting to. Defaults
  to 1.

##### set rescale\_svg!
Toggle the [rescale\_svg]({{
site.baseurl}}/docs/configuration#rescale-svg) setting.

##### set sharpness
**Syntax:** <t class="command"><b>:set sharpness</b> <i>[value]</i></t>

Set the sharpness of the current image.

Enter manipulate mode if not there yet.

**Optional arguments:**
* <i class="command">value</i>: Value between -127 and 127 to set the sharpness
  to. Defaults to 0.

##### set show\_hidden!
Toggle the [show\_hidden]({{
  site.baseurl}}/docs/configuration#show-hidden) setting.

##### set slideshow\_delay
**Syntax:** <t class="command"><b>:set slideshow_delay</b> <i>[value]</i></t>

Set the slideshow delay.

**Optional arguments:**
* <i class="command">value</i>: Value to set the slideshow delay to.  Defaults
  to the [slideshow\_delay]({{ site.baseurl
}}/docs/configuration#slideshow-delay) setting.

##### set statusbar!
Toggle the statusbar.

**Note:** Even if the statusbar is hidden, error messages are still displayed.

##### shrink\_lib
**Syntax:** <t class="command"><b>:shrink_lib</b> <i>[value]</i></t>

Decrease the library width.

**Optional arguments:**
* <i class="command">value</i>: Value to decrease width by. Defaults to 20.

**Count:** Multiply [value] by [count].

##### slideshow
Toggle the slideshow.

**Count:** Set the slideshow delay to [count].

##### slideshow\_delay
**Syntax:** <t class="command"><b>:slideshow_delay</b> <i>value</i></t>

Change the value of the slideshow delay.

**Positional arguments:**
* <i class="command">value</i>: Change by value.

**Count:** Multiply [value] by [count].

**Note:** This decreases or increases by the given value. If you want to set
the delay to a specific value, use [set slideshow_delay](#set-slideshow_delay)
instead.

##### tag\_write
**Syntax:** <t class="command"><b>:tag_write</b> <i>tagname</i></t>

Write the names of all currently marked images to a tagfile.

If the file does not exist, create it. If it does, append the names to
the tagfile if they are not in it already.

**Positional arguments:**
* <i class="command">tagname</i>: Name of the tagfile to write to.

##### tag\_load
**Syntax:** <t class="command"><b>:tag_load</b> <i>tagname</i></t>

Load all images in a tagfile into image mode.

**Positional arguments:**
* <i class="command">tagname</i>: Name of the tagfile to load.

##### tag\_remove
**Syntax:** <t class="command"><b>:tag_remove</b> <i>tagname</i></t>

Delete a tagfile.

**Positional arguments:**
* <i class="command">tagname</i>: Name of the tagfile to delete.

##### thumbnail
Toggle thumbnail mode.

##### undelete
**Syntax:** <t class="command"><b>:undelete</b> <i>basename</i></t>

Undelete the image with <i class="command">basename</i>.

This moves it from the trash directory back to its original path.

**Positional arguments:**
* <i class="command">basename</i>: Unique basename of the image to undelete as
  it is in the trash directory.


##### unfocus\_library
Focus the widget last focused before the library.

##### version
Display pop-up with version information.

Includes version number, link to the website and license.

##### zoom\_in
**Syntax:** <t class="command"><b>:zoom_in</b> <i>[steps]</i></t>

Zoom in.

**Optional arguments:**
* <i class="command">steps</i>: Zoom in by the number of steps.

**Count:** Zoom in by [count] <i class="command">steps</i>.

**Note:** Numbers prepended by 0 are parsed as decimals. For example 033 is
parsed as 0.33. This allows giving a decimal step via [count].

##### zoom\_out
**Syntax:** <t class="command"><b>:zoom_out</b> <i>[steps]</i></t>

Zoom out.

**Optional arguments:**
* <i class="command">steps</i>: Zoom out by the number of steps.

**Count:** Zoom out by [count] <i class="command">steps</i>.

**Note:** Numbers prepended by 0 are parsed as decimals. For example 033 is
parsed as 0.33. This allows giving a decimal step via [count].

##### zoom\_to
**Syntax:** <t class="command"><b>:zoom_to</b> <i>percent</i></t>

Zoom image to a given percentage.

**Positional arguments:**
* <i class="command">percent</i>: Percentage to zoom to.

**Count:** Zoom to [count].

**Note:** Numbers prepended by 0 are parsed as decimals. For example 033 is
parsed as 0.33. This allows giving a decimal percentage via [count].
