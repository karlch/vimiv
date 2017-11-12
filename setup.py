#!/usr/bin/env python3
# encoding: utf-8

from setuptools import setup, Extension

# C extensions
enhance_module = Extension("vimiv._image_enhance", sources = ["c-lib/enhance.c"])

setup(
    name="vimiv",
    version="0.9",
    packages=['vimiv'],
    ext_modules = [enhance_module],
    scripts=['vimiv/vimiv'],
    install_requires=['pillow', 'PyGObject'],
    description="An image viewer with vim-like keybindings",
    license="MIT",
    url="https://github.com/karlch/vimiv",
)
