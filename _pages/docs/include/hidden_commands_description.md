##### clear\_status
Clear any numbers or messages from the statusbar.

##### command
**Syntax:** <t class="command"><b>:command</b> <i>[text]</i></t>

Enter the command line.

**Optional arguments:**
* <i class="command">text</i>: Set text of the command line.

##### scroll
**Syntax:** <t class="command"><b>:scroll</b> <i>direction</i></t>

Scroll image or thumbnail.

**Positional arguments:**
* <i class="command">direction</i>: The direction to scroll in. One of <i class
  = "command">hjklHJKL</i>. Capitals scroll to the far end.

**Count:** Scroll [count] times.

##### scroll\_lib
**Syntax:** <t class="command"><b>:scroll_lib</b> <i>direction</i></t>

Scroll the library.

**Positional arguments:**
* <i class="command">direction</i>: The direction to scroll in. One of <i class
  = "command">hjkl</i>.

**Count:** Scroll [count] times.

##### search
**Syntax:** <t class="command"><b>:search</b> <i>text</i></t>

Search for text in the current filelist.

Search through the current filelist for matching text. Focus the next
result. Per default search is [case-sensitive]({{ site.baseurl
}}/documentation/configuration#search-case-sensitive) and [incsearch]({{
site.baseurl }}/documentation/configuration#incsearch) is enabled.

**Positional arguments:**
* <i class="command">text</i>: The text to search for.

##### search\_next
Navigate to the next search result.

**Count:** Move [count] search results forward.

##### search\_prev
Navigate to the previous search result.

**Count:** Move [count] search results backward.

##### history\_down
Go down by one in command line history.

Does a substring search with the current text in the command line.

**Note:** Only makes sense in COMMAND section.

##### history\_up
Go up by one in command line history.

Does a substring search with the current text in the command line.

**Note:** Only makes sense in COMMAND section.

##### discard\_command
Leave the command line discarding currently entered text.

**Note:** Only makes sense in COMMAND section.

##### complete
Start command line completion.

Complete to best match if any. Then select the next item in the
completion menu.

**Note:** Only makes sense in COMMAND section.

##### complete\_inverse
Start command line completion.

Complete to best match if any. Then select the previous item in the
completion menu.

**Note:** Only makes sense in COMMAND section.

##### slider
**Syntax:** <t class="command"><b>:slider</b> <i>[value]</i></t>

Change the value of the currently focused slider.

**Optional arguments:**
* <i class="command">value</i>: Change by value. Defaults to 1.

**Note:** Only makes sense in MANIPULATE section.

**Count:** Multiply [value] by [count].

##### focus\_slider
**Syntax:** <t class="command"><b>:focus_slider</b> <i>name</i></t>

Focus one of the manipulate slider.

**Positional arguments:**
* <i class="command">name</i>: Name of the slider. One of <i
  class="command">bri/con/sat</i>.

**Note:** Only makes sense in MANIPULATE section.
