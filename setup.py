#!/usr/bin/env python3
# encoding: utf-8
from setuptools import setup
import vimiv

setup(
    name = "vimiv",
    version = vimiv.__version__
    packages = ['vimiv'],
    scripts = ['vimiv/vimiv'],
    install_requires = ['pillow', 'PyGObject'],
    description = "An image viewer with vim-like keybindings",
    license = vimiv.__license__,
    url = "https://github.com/karlch/vimiv",
)
