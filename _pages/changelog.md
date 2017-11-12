---
layout: page
title: Changelog
permalink: /changelog
---

The most important changes between versions are listed here.

#### v0.9.0 (unreleased)
* Async loading of images and gifs
* Overzoom setting is now float instead of bool
* Improve handling of animated gifs:
  * Allow scaling
  * Add autoplay\_gifs option
* Rewrite the generation of the dictionary used for storing internal commands
* Also read configuration files from $XDG_CONFIG_HOME/vimiv/
* Implement the freedesktop standard for thumbnail management (thanks woefe),
  this leads to these changes:
  * Remove the settings cache_thumbnails, thumbsize and thumb_maxsize
  * New default_thumbsize setting
  * Remove the clear_thumbs command
* Thumbnail generation and scaling is now asynchronous (thanks woefe) 
* Move data (history, logfile and tags) to $XDG_DATA_HOME/vimiv/
* Implement freedesktop's trash specification, this leads to these changes:
  * Default trash directory is now $XDG_DATA_HOME/Trash
  * Remove the clear_trash command as this may delete far more than only
    vimiv's trash. If anyone has hard feelings about this, it is very easy to
    bind to an alias.
  * Add an :undelete command to move images back to their original path.
* Large code changes to decouple vimiv
* New way to handle settings:
  * Settings are now stored in one global class for increased flexibility
  * Rewrite of the :set command which now simply changes a setting in the
    storage
  * Changed setting names to reflect new behaviour:
    * autoplay\_gifs renamed to play\_animations
    * show\_library renamed to start\_show\_library
  * The set brightness/contrast/sharpness commands are now called edit
    brightness/contrast/sharpness.
  * All commands that started with set are now merged into a single set command
    leading to different command names for some of them.
* Get rid of PIL as dependency:
  * GdkPixbuf used for all simple transformations
  * A small C-extension deals with brightness and contrast
  * Support for editing sharpness was dropped
  * Editing saturation is now possible
  * New optional dependency `gexiv2` for Exif support
* New autosave\_images setting
* New :w and :wq commands
* Add appdata file (thanks Ankur Sinha!)

#### v0.8
* Rewrite large parts to make vimiv a Gtk.Application
* Rewrite parser as Gtk parser
* Rewrite open using the Gtk.Application do_open method
* Add command copy to clipboard which copies the currently selected
  image name to clipboard or primary depending on the copy_to_primary
  setting. The selection can be toggled using the set clipboard!
  command.
* Default flip keybindings to | and _ because y and Y are used for the copy
  method
* Implement --temp-basedir flag
* Rewrite command line completion with a Gtk.TreeView This allows the usage of
  native Gtk filtering and showing some information on internal commands.
  Downside: no more completion for external commands as the Gtk.ListStore model
  involved is not performant enough for large amounts of data.
* Rename and merge commands:
  * zoom_thumb_in/\_out merged into zoom_in/\_out
  * cmd_history\_\* renamed to history\_\*
  * left/down/up/right merged into scroll hjkl
  * bri\_/con\_/sha\_focus merged into focus_slider bri/con/sha
  * slideshow\_inc/\_dec merged into slideshow_delay value
* Allow setting text upon command line entry via command text.
* Improve messages from the statusbar. They now come in three flavours: error,
  warning and info and set a different color indicater for each one.
* Introduce tilde_in_statusbar setting to collapse $HOME to ~ in the library
  statusbar.
* Introduce clear_status command to remove any numbers or messages from the
  statusbar and reset search.
* Create thumbnails directly with Gdk.Pixbuf.new_from_file_at_scale
* Only edit image file when leaving image after calling rotate/flip
* Make thumbnail padding configurable
* Add a simple log file written to basedir/vimiv.log
* --debug flag now writes useful information to the log file.
* Allow passing count for more functions and clear count if the function does
  not support it
* Implement simple mouse support
* Deprecate combined keybinding sections like IM_LIB, GENERAL, ...

#### v0.7.3
* Bugfix release
* Fix thumbnail creation for input files with dot (thanks aszlig)
* Use native python to generate list of external commands (thanks aszlig)
* Do not use command line arguments in test mode (thanks aszlig)
* Catch broken symlinks in the library and filter them

#### v0.7.2
* Add search in thumbnail mode
* Make it possible to go straight to thumbnail mode from library
* t is bound to thumbnail mode in library now instead of toggling show_hidden
  by default
* Fix fullscreen behaviour in some DEs
* Minor code optimization and tweaks
* Display useful error messages when a setting in the configfile is invalid.
* Add :version command and --version flag

#### v0.7.1
* Bugfix release
* Always start search at current position
* Fix incsearch when search has no results
* Fix search problems when image and library are open
* Failed thumbnails now show up as error icon

#### v0.7
* Add zooming of thumbnails
* Add support for aliases
* Compatability with Gtk 3.22
* Add incsearch

#### v0.6.1
* Bugfix release after implementing a testsuite
* Stop mark_between from marking directories
* Fix clear_thumbs
* Fix leaving command line on double tab
* Fix set library_width
* grow\_/shrink\_lib allow an argument
* Implemented error message pop-up for fatal errors at startup
* Add icon for vimiv
* Improve scrolling in library and thumbnail mode
* Library border now set with Gtk.Separator, border_color is no longer in
  config
* Proper pause and play of animated Gifs

#### v0.6
* Major rebase of code rewriting vimiv as python module
* Add option to disable thumbnail cache
* Handle symlinks neatly: do not follow them into their parent directory
* Open images regardless of extension
* Inform when slideshow reaches beginning again
* Automatically resize thumbnail grid
* Much better tab completion

#### v0.5
* Pipe to vimiv
* Built-in Tag support
* Multithreading of external commands
* New configfiles vimivrc and keys.conf instead of vimivrc.py
* Search results navigable with N and P
* Search can be case insensitive
* Implement search highlighting

#### v0.4.1
* Let external shell handle external arguments, allows for pipes, ...
* Colon and slash displayed in command line for commands and searching
* Command history now with arrow keys and supports substring search
* All external commands can be tab-completed
* Follow symbolic links to their directory
* Escape sequences as expected for % and \*

#### v0.4
* Add a command line
* Add various internal commands for the command line
* Tab-completion
* Solve a minor bug: when manipulating images and returning back to the value 0
  in any of the sliders the image wouldn't be updated before
* Arrow keys now support prefixing by numbers

#### v0.3
* Vimiv is now single window
* Catch some more exceptions
* Update the statusbar
* Improve manipulation of images

#### v0.2
* Fullscreen now works for both the main window and the library pop-up
* Images and directories are distinguished in the library
* An extra keyhandler for the library
* Different handling of showing directory size, highly increases library
  performance
* Remember last position in library
* Add the cmd_handler
* If a folder is given as path, open it in the library
* Prefix zoom with numbers
* Marking images much more useful
* Handling of some standard keybindings (^C, ^Q)

#### v0.1
* Initial release
