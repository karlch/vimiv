# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test settings.py for vimiv's test suite."""

import os
from unittest import TestCase, main

from vimiv.exceptions import NotABoolean, NotANumber, StringConversionError
from vimiv import settings


class BoolSettingTest(TestCase):
    """Test the Setting class in its default boolean implementation."""

    @classmethod
    def setUpClass(cls):
        cls.name = "is_true"
        cls.default = True
        cls.setting = settings.BoolSetting(cls.name, cls.default)

    def test_init(self):
        """Test initializing a setting."""
        self.assertTrue(self.setting.get_default())
        self.assertEqual(self.setting.name, self.name)
        self.assertTrue(self.setting.is_default())
        self.assertTrue(self.setting.get_value())

    def test_override(self):
        """Test overriding a boolean setting."""
        self.setting.override("no")
        self.assertFalse(self.setting.get_value())
        self.assertFalse(self.setting.is_default())
        self.assertTrue(self.setting.get_default())
        self.setting.override("yes")
        self.assertTrue(self.setting.get_value())
        self.setting.override("FaLsE")
        self.assertFalse(self.setting.get_value())
        self.setting.override("trUE")
        self.assertTrue(self.setting.get_value())


class IntSettingTest(TestCase):
    """Test the IntSetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "number"
        cls.default = 3
        cls.setting = settings.IntSetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding an integer setting."""
        self.setting.override("5")
        self.assertEqual(self.setting.get_value(), 5)
        self.assertFalse(self.setting.is_default())
        self.setting.override("0.")
        self.assertEqual(self.setting.get_value(), 0)

    def test_fail_override(self):
        """Fail overriding an integer setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "-2")
        self.assertRaises(StringConversionError, self.setting.override,
                          "42.42")
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "True")


class FloatSettingTest(TestCase):
    """Test the FloatSetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "number"
        cls.default = 3.3
        cls.setting = settings.FloatSetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding a float setting."""
        self.setting.override("5.5")
        self.assertAlmostEqual(self.setting.get_value(), 5.5)
        self.assertFalse(self.setting.is_default())

    def test_fail_override(self):
        """Fail overriding a float setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "-12.12")
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "True")


class ThumbnailSizeSettingTest(TestCase):
    """Test the ThumbnailSizeSetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "int_tuple"
        cls.default = (128, 128)
        cls.setting = settings.ThumbnailSizeSetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding a thumbnail size setting."""
        self.setting.override("(256, 256)")
        self.assertEqual(self.setting.get_value(), (256, 256))
        self.assertFalse(self.setting.is_default())

    def test_fail_override(self):
        """Fail overriding a thumbnail size setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100 100")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100,-100")
        self.assertRaises(StringConversionError, self.setting.override,
                          "(100, 256)")
        self.assertRaises(StringConversionError, self.setting.override,
                          "(512, 256)")
        self.assertRaises(StringConversionError, self.setting.override,
                          "(100, 100)")


class GeometrySettingTest(TestCase):
    """Test the GeometrySetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "geometry"
        cls.default = (800, 600)
        cls.setting = settings.GeometrySetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding a geometry setting."""
        self.setting.override("500x500")
        self.assertEqual(self.setting.get_value(), (500, 500))
        self.assertFalse(self.setting.is_default())

    def test_fail_override(self):
        """Fail overriding a geometry setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100 100")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100x-100")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100.5x100")


class DirectorySettingTest(TestCase):
    """Test the DirectorySetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "directory"
        cls.default = os.getcwd()
        cls.setting = settings.DirectorySetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding a directory setting."""
        new_dir = os.path.dirname(os.getcwd())
        self.setting.override(new_dir)
        self.assertEqual(self.setting.get_value(), new_dir)
        self.assertFalse(self.setting.is_default())

    def test_fail_override(self):
        """Fail overriding a directory setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "100")
        self.assertRaises(StringConversionError, self.setting.override,
                          "/foo/bar/baz")


class MarkupSettingtest(TestCase):
    """Test the MarkupSetting class."""

    @classmethod
    def setUpClass(cls):
        cls.name = "markup"
        cls.default = '<span foreground="#875FFF">'
        cls.setting = settings.MarkupSetting(cls.name, cls.default)

    def test_override(self):
        """Test overriding a markup setting."""
        new_markup = '<span foreground="#FFFFFF">'
        self.setting.override(new_markup)
        self.assertEqual(self.setting.get_value(), new_markup)
        self.assertFalse(self.setting.is_default())

    def test_fail_override(self):
        """Fail overriding a markup setting."""
        self.assertRaises(StringConversionError, self.setting.override,
                          "hello")
        self.assertRaises(StringConversionError, self.setting.override,
                          "<span hi")
        self.assertRaises(StringConversionError, self.setting.override,
                          "hi>")


class SettingStorageTest(TestCase):
    """Test the SettingStorage class."""

    @classmethod
    def setUpClass(cls):
        cls.storage = settings.SettingStorage()

    def test_default_setting(self):
        """Test if defaults are set correctly in storage."""
        defaults = {"start_fullscreen": False,
                    "start_slideshow": False,
                    "slideshow_delay": 2,
                    "shuffle": False,
                    "display_bar": True,
                    "default_thumbsize": (128, 128),
                    "geometry": (800, 600),
                    "search_case_sensitive": True,
                    "incsearch": True,
                    "recursive": False,
                    "rescale_svg": True,
                    "overzoom": 1,
                    "copy_to_primary": False,
                    "commandline_padding": 6,
                    "thumb_padding": 10,
                    "completion_height": 200,
                    "play_animations": True,
                    "start_show_library": False,
                    "library_width": 300,
                    "expand_lib": True,
                    "border_width": 0,
                    "markup": '<span foreground="#875FFF">',
                    "show_hidden": False,
                    "desktop_start_dir": os.path.expanduser("~"),
                    "file_check_amount": 30,
                    "tilde_in_statusbar": True}
        for setting in defaults:
            storage_setting = self.storage[setting]
            self.assertEqual(storage_setting.get_value(), defaults[setting])

    def test_override_setting(self):
        """Override setting directly in storage."""
        self.storage.override("play_animations", "false")
        self.assertEqual(self.storage["play_animations"].get_value(), False)
        # Override with default value
        self.storage.override("play_animations")
        self.assertEqual(self.storage["play_animations"].get_value(), True)

    def test_fail_methods(self):
        """Fail methods in setting storage."""
        self.assertRaises(NotABoolean,
                          self.storage.toggle, "border_width")
        self.assertRaises(NotANumber,
                          self.storage.add_to, "show_hidden", "1", "1")

    def test_access_unavailable_setting_in_storage(self):
        """Try to access a setting that does not exist in storage."""
        self.assertRaises(settings.SettingNotFoundError,
                          self.storage.__getitem__, "hello")


if __name__ == "__main__":
    main()
