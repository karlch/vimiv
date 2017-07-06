# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test settings.py for vimiv's test suite."""

import os

from unittest import TestCase, main

from vimiv import settings


class BoolSettingTest(TestCase):
    """Test the Setting class in its default boolean implementation."""

    @classmethod
    def setUpClass(cls):
        cls.name = "is_true"
        cls.default = True
        cls.setting = settings.Setting(cls.name, cls.default)

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

    def test_fail_override(self):
        """Fail overriding an integer setting."""
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "-2")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "42.42")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "hello")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
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
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "-12.12")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "hello")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "True")


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
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "hello")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "100 100")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "100x-100")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
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
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "hello")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "100")
        self.assertRaises(settings.WrongSettingValue, self.setting.override,
                          "/foo/bar/baz")


if __name__ == "__main__":
    main()
