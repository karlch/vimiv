---
layout: page
title: For Developers
permalink: /docs/develop
---

### Contributing

You want to contribute? Great!

This page contains the guidelines for contributing to vimiv and some helpful
information to get you started. If any of the guidelines stop you from
contributing, please do so anyway. They are only here to make my life easier, I
will happily try to fix any problems myself.

If you run into any issues, feel free to contact me under
[karlch@protonmail.com](mailto:karlch@protonmail.com).

### Finding something to do
You probably already know what you want to work on as you are reading this
page. If you want to implement a new feature, it might be a good idea to open a
feature request on the [issue tracker](https://github.com/karlch/vimiv/issues)
or send me an [email](mailto:karlch@protonmail.com) first. Otherwise you might
be dissapointed if I do not accept your pull request because I do not want this
feature added.

A great way to help is to work on
[open issues](https://github.com/karlch/vimiv/issues).

As this is my first larger project, reviewing and improving the code itself
is another possibility to contribute. Especially the testsuite probably
needs improvement.

If you do not want to code anything, you can still contribute by:
* Improving the documentation
* Improving the keybinding cheatsheet
* Working on this website and on any graphics like the icon

### Style and tests

Newly introduced code should not break any existing tests or modify them
according to the new behaviour. If you introduce a new feature, writing a
test for it would be awesome!

The tests can be run with
```
$ make test
```
This simply calls the script
<a href="https://github.com/karlch/vimiv/blob/master/scripts/run_tests.sh" class="filename">run_tests.sh</a>
which starts by cloning the images used for tests from the branch
<a href="https://github.com/karlch/vimiv/tree/testimages">testimages</a>. It
starts Xvfb on display :42. The testsuite is then run with
<a href="https://nose.readthedocs.io/en/latest/">nosetests</a>.

Similarly the stlye checkers are run with
```
$ make lint
```
which calls
<a href="https://www.pylint.org/">pylint</a>,
<a href="http://www.pydocstyle.org/en/latest/">pydocstyle</a> and
<a href="https://pycodestyle.readthedocs.io/en/latest/#">pycodestyle</a>
for all .py files in the vimiv and tests directories. They are configured in
<a href="https://github.com/karlch/vimiv/blob/master/.pylintrc" class="filename">.pylintrc</a>,
<a href="https://github.com/karlch/vimiv/blob/master/.pydocstylerc" class="filename">.pydocstylerc</a> and
<a href="https://github.com/karlch/vimiv/blob/master/.pycodestyle" class="filename">.pycodestyle</a>
respectively.

As bonus
```
$ make spellcheck
```
runs spell checking for docstrings and comments using enchant. This does not
work well when referencing variables, methods, ... but has caught quite a few
typos for me. If the only errors remaining are variable names etc., calling
```
$ make spellcheck_add_unknown
```
will add them to the whitelist.

### Test requirements
Additionally to the standard requirements to get vimiv up and running, the
following programs are necessary to run the testsuite and the style
checkers.

###### For the tests
* nosetests
* xvfb
* python coverage

###### For the style checkers
* pylint
* pydocstyle
* pycodestyle
* optional: enchant with hunspell_en for spellchecking
