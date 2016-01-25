### Contributing to vimiv
You want to contribute? Great! Here are some general recommendations.
I try to comment the code fairly well and the code tries to follow pep8
standards. So if you want to contribute please try to do so as well.

## TODO List
These are some topics that are on my TODO List. They are marked in the code.
If you would like to solve one of these or have ideas how to, awesome and
thanks!

#### Proper toggling of animated Gifs
Currently if the animation of an animated Gif is stopped the first frame is
displayed as static image. It would be much nicer to show the current frame and
then start playing from there again.

The reason therefore is the way Gdk.PixbufAnimation.get\_static\_image() is
handled.

The animation state of Gifs gets handled in the function update\_image and the
animation state is toggled via the function animation\_toggle.

#### Better handling of scrolling in thumbnail mode
Currently the actual scrolling in thumbnail mode is done using the function
thumbnail\_scroll. It scrolls the window by the step which is calculated in
thumbnail\_move. This does not work properly because the size of thumbnails is
not constant.

It would be much nicer if the Gtk.IconView.scroll\_to\_path function would work.
It doesn't do anything though because the IconView thinks all thumbnails are
visible, even if they are not for the user.

## New features
If you would like to implement a new feature it might be a good idea to send me
an email to "christian dot karl at protonmail dot com" to ask if I would like to
see it implemented. Otherwise you might be disappointed afterwards if I do not
accept your pull request. In general though I am very happy about any interest
in vimiv!

## Open issues
Another great way to help is to work on open issues. Some of these obviously
overlap with my TODO list.

## Testing and bug reporting
Fairly obvious. Just open an issue or send me an email. If you feel adventurous,
you can test the unreleased branches depending on whether a new version is
currently under development.
