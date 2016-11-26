## Changelog
The most important changes between the versions are listed here.

#### v0.7.2 (unreleased)
* Add search in thumbnail mode
* Make it possible to go straight to thumbnail mode from library
* t is bound to thumbnail mode in library now instead of toggling show\_hidden
  per default
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
* Stop mark\_between from marking directories
* Fix clear\_thumbs
* Fix leaving commandline on double tab
* Fix set library\_width
* grow\_/shrink\_lib allow an argument
* Implemented error message pop-up for fatal errors at startup
* Add icon for vimiv
* Improve scrolling in library and thumbnail mode
* Library border now set with Gtk.Separator, border\_color is no longer in
  config
* Proper pause and play of animated Gifs

#### v0.6
* Major rebase of code rewriting vimiv as python module
* Add option to disable thumbnail cache
* Handle symlinks neatly (-> do not follow them into their parent directory)
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
* Escape sequences as expected for % and *

#### v0.4
* Added a command line
* Added various internal commands for the command line
* Tab-completion
* Solved a minor bug: when manipulating images and returning back to the value 0
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
* Add the cmd\_handler
* If a folder is given as path, open it in the library
* Prefix zoom with numbers
* Marking images much more useful
* Handling of some standard keybindings (^C, ^Q)

#### v0.1
* initial commit
