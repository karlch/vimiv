#!/usr/bin/env python3
# encoding: utf-8
from setuptools import setup

setup(
    name = "vimiv",
    version = "0.8.1dev0",
    packages = ['vimiv'],
    scripts = ['vimiv/vimiv'],
    install_requires = ['pillow', 'PyGObject'],
    description = "An image viewer with vim-like keybindings",
    license = "MIT",
    url = "https://github.com/karlch/vimiv",
)
