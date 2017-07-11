Settings are configured in the vimivrc file. This file is separated into four
sections:

* GENERAL
* LIBRARY
* EDIT
* ALIASES

The first three sections group settings, the fourth is used to define aliases.
What each setting means and what values are possible is explained below:

#### GENERAL

|Setting|Value|Default|Description|
|-------|-----|-------|-----------|
|start_fullscreen|Bool|no|If yes, start fullscreen.|
|-------|-----|-------|-----------|
|start_slideshow|Bool|no|If yes, start slideshow at startup.|
|-------|-----|-------|-----------|
|<a name="slideshow-delay" class="anchor">slideshow_delay</a>|Float|2.0|Specify the delay for the slideshow.|
|-------|-----|-------|-----------|
|shuffle|Bool|no|If yes, shuffle the images in the filelist randomly.|
|-------|-----|-------|-----------|
|display_bar|Bool|yes|If yes, show the statusbar at the bottom. Else hide it.Note that error messages are still displayed, even if the statusbar is hidden.|
|-------|-----|-------|-----------|
|default_thumbsize|Tuple|(128,128)|Size for the thumbnails in the form of (x, y).|
|-------|-----|-------|-----------|
|geometry|String|800x600|String in the form of "WIDTHxHEIGHT" specifying the default size for the window. Note that not all window managers respect this setting.|
|-------|-----|-------|-----------|
|recursive|Bool|no|If yes, search the given directory recursively for images at startup.|
|-------|-----|-------|-----------|
|<a name="rescale-svg" class="anchor">rescale_svg</a>|Bool|yes|If yes, rescale vector graphics automatically by reloading the image. Otherwise simply zoom as if they were a normal image.|
|-------|-----|-------|-----------|
|<a name="overzoom" class="anchor">overzoom</a>|Float|1.0|Float defining the maximum amount to scale images up by trying to fit the window when first loading the image.|
|-------|-----|-------|-----------|
|<a name="search-case-sensitive" class="anchor">search_case_sensitive</a>|Bool|yes|If yes, search case sensitively. Ignore case otherwise.|
|-------|-----|-------|-----------|
|<a name="incsearch" class="anchor">incsearch</a>|Bool|yes|If yes, search incrementally when typing.|
|-------|-----|-------|-----------|
|<a name="copy-to-primary" class="anchor">copy_to_primary</a>|Bool|no|If yes, copy to primary selection instead of clipboard.|
|-------|-----|-------|-----------|
|commandline_padding|Int|6|Padding to use in the command line and statusbar.|
|-------|-----|-------|-----------|
|thumb_padding|Int|10|Padding to use between thumbnails. Note: Additionally to the padding column spacing gets updated dynamically to best fit the current window width.|
|-------|-----|-------|-----------|
|completion_height|Int|200|Height of the completion menu when showing command line completions.|
|-------|-----|-------|-----------|
|play\_animations|Bool|yes|If yes, animated gif are played. Otherwise stay at the first/current frame.|
|-------|-----|-------|-----------|

#### LIBRARY

|Setting|Value|Default|Description|
|-------|-----|-------|-----------|
|start_show_library|Bool|no|If yes, always show library at start-up.|
|-------|-----|-------|-----------|
|<a name="library-width" class="anchor">library_width</a>|Int|300|Default width of the library when an image is open.|
|-------|-----|-------|-----------|
|expand_lib|Bool|yes|If yes, automatically expand the library to full window size if no image is open.|
|-------|-----|-------|-----------|
|border_width|Int|0|Width of the border separating library and image.|
|-------|-----|-------|-----------|
|markup|String|&lt;span foreground="#875FFF"&gt;|Markup used to highlight search results. This must be a correct markup opening in the form of one &lt;span ...&gt; element as it gets closed with &lt;/span&gt;|
|-------|-----|-------|-----------|
|<a name="show-hidden" class="anchor">show_hidden</a>|Bool|no|If yes, show hidden files in the library and open hidden images.|
|-------|-----|-------|-----------|
|desktop_start_dir|String|~|The directory in which vimiv should start if opened via the .desktop file.|
|-------|-----|-------|-----------|
|file_check_amount|Int|30|The amount of files vimiv should check in a directory for whether they are images or not. This affects the size column of directories in the library. As soon as this number is reached, checks are stopped and a + is appended, e.g. 30+. A higher number increases precision and information at the cost of speed.|
|-------|-----|-------|-----------|
|tilde_in_statusbar|Bool|yes|If yes, collapse $HOME to ~ in the statusbar in the library.|
|-------|-----|-------|-----------|

#### EDIT

|Setting|Value|Default|Description|
|-------|-----|-------|-----------|
|<a name="autosave-images" class="anchor">autosave_images</a>|Bool|yes|If yes, automatically save rotated/flipped images to disk. Otherwise to keep changes :w must be called explicitly.|
|-------|-----|-------|-----------|

#### ALIASES

It is possible to configure aliases for the command line in this section.
An alias is defined in the form of:

<t class="command"><b>aliasname</b>: <i>command</i></t>

See also: the <a href="{{ site.baseurl }}/docs/keybindings_commands#alias">alias command</a>.
