# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Configparser Tests for vimiv's testsuite."""

import configparser
import os
import sys
import tempfile
from unittest import TestCase, main

from gi import require_version
require_version('GLib', '2.0')
from gi.repository import GLib

import vimiv.config_parser as parser

from vimiv.settings import settings


class ConfigparserTest(TestCase):
    """Configparser Tests."""

    @classmethod
    def setUpClass(cls):
        # Catch stdout for error messages
        if not hasattr(sys.stdout, "getvalue"):
            cls.fail(cls, "Need to run test in buffered mode.")
        cls.tmpdir = tempfile.TemporaryDirectory(prefix="vimivtests-")
        cls.configdir = cls.tmpdir.name
        cls.configfile_counter = 0  # Used to always create unique new filenames
        cls.keybindings = {}
        cls.keybindings["IMAGE"] = {"a": "autorotate"}
        cls.keybindings["THUMBNAIL"] = {"a": "autorotate"}
        cls.keybindings["LIBRARY"] = {"a": "autorotate"}
        cls.keybindings["MANIPULATE"] = {"a": "autorotate"}
        cls.keybindings["COMMAND"] = {"Tab": "complete"}

    def check_defaults(self, settings_to_check):
        """Check is settings contain default values."""
        for setting in settings_to_check:
            self.assertTrue(setting.is_default())

    def test_parse_config_empty(self):
        """Parse an empty configfile."""
        # Should set default values
        path = os.path.join(self.configdir, "empty_vimivrc")
        with open(path, "w") as f:
            f.write("")
        parser.parse_config(path, running_tests=True)
        self.check_defaults(settings)

    def test_unexisting_configfile(self):
        """Parse a non-existing configfile."""
        path = os.path.join(self.configdir, "this_file_does_not_exist")
        # Should ignore it and set default values
        read_settings = parser.parse_config(path, running_tests=True)
        self.check_defaults(read_settings)

    def test_correct_configfile(self):
        """Parse correct non-default configfile with all settings."""
        override = {"GENERAL": {"start_fullscreen": "yes",
                                "start_slideshow": "yes",
                                "shuffle": "yes",
                                "display_bar": "no",
                                "default_thumbsize": "(256, 256)",
                                "geometry": "400x400",
                                "recursive": "yes",
                                "rescale_svg": "yes",
                                "overzoom": "1.5",
                                "search_case_sensitive": "yes",
                                "incsearch": "no",
                                "copy_to_primary": "no",
                                "commandline_padding": 0,
                                "completion_height": 100},
                    "LIBRARY": {"show_library": "yes",
                                "library_width": "200",
                                "expand_lib": "no",
                                "border_width": "12",
                                "markup": "<span foreground=\"#FF0000\">",
                                "show_hidden": "no",
                                "desktop_start_dir": "~/.local",
                                "file_check_amount": "10",
                                "tilde_in_statusbar": "no"},
                    "ALIASES": {"testalias": "zoom_in"}}
        configfile = self.create_configfile(new_settings=override)
        parser.parse_config(configfile, running_tests=True)
        self.assertEqual(settings["start_fullscreen"].get_value(), True)
        self.assertEqual(settings["start_slideshow"].get_value(), True)
        self.assertEqual(settings["shuffle"].get_value(), True)
        self.assertEqual(settings["display_bar"].get_value(), False)
        self.assertEqual(settings["default_thumbsize"].get_value(), (256, 256))
        self.assertEqual(settings["geometry"].get_value(), (400, 400))
        self.assertEqual(settings["recursive"].get_value(), True)
        self.assertEqual(settings["rescale_svg"].get_value(), True)
        self.assertEqual(settings["overzoom"].get_value(), 1.5)
        self.assertEqual(settings["search_case_sensitive"].get_value(), True)
        self.assertEqual(settings["incsearch"].get_value(), False)
        self.assertEqual(settings["copy_to_primary"].get_value(), False)
        self.assertEqual(settings["commandline_padding"].get_value(), 0)
        self.assertEqual(settings["completion_height"].get_value(), 100)
        self.assertEqual(settings["show_library"].get_value(), True)
        self.assertEqual(settings["library_width"].get_value(), 200)
        self.assertEqual(settings["expand_lib"].get_value(), False)
        self.assertEqual(settings["border_width"].get_value(), 12)
        self.assertEqual(
            settings["markup"].get_value(),
            GLib.markup_escape_text("<span foreground=\"#FF0000\">"))
        self.assertEqual(settings["show_hidden"].get_value(), False)
        self.assertEqual(settings["desktop_start_dir"].get_value(),
                         os.path.expanduser("~/.local"))
        self.assertEqual(settings["file_check_amount"].get_value(), 10)
        self.assertEqual(settings["tilde_in_statusbar"].get_value(), False)
        # self.assertIn("testalias", aliases.keys())
        # self.assertEqual(aliases["testalias"], "zoom_in")

    def test_broken_configfiles(self):
        """Parse broken configfiles.

        Check for the error message in stdout. The parsed settings should be
        default as no valid updates are made.
        """
        # Invalid because it does not have the setting: value structure
        text = "[GENERAL]\nsome useless text\n"
        configfile = self.create_configfile(text=text)
        parsed_settings = parser.parse_config(configfile, running_tests=True)
        # pylint:disable=no-member
        output = sys.stdout.getvalue().strip()
        self.assertIn("Source contains parsing errors", output)
        self.check_defaults(parsed_settings)

        # Is not plain text but rather a binary
        parsed_settings = parser.parse_config("vimiv/testimages/arch-logo.png",
                                              running_tests=True)
        output = sys.stdout.getvalue().strip()
        self.assertIn("Could not decode configfile", output)
        self.check_defaults(parsed_settings)

        # Start without a section header before the settings
        text = "shuffle: yes\n"
        configfile = self.create_configfile(text=text)
        parsed_settings = parser.parse_config(configfile, running_tests=True)
        output = sys.stdout.getvalue().strip()
        self.assertIn("Invalid configfile", output)
        self.check_defaults(parsed_settings)

    def test_parse_keys(self):
        """Parse a correct minimal keyfile."""
        keyfile = self.create_keyfile(self.keybindings)
        parsed_bindings = parser.parse_keys(keyfiles=[keyfile],
                                            running_tests=True)
        # Checking one should be enough
        image = parsed_bindings["IMAGE"]
        self.assertEqual(self.keybindings["IMAGE"]["a"], image["a"])

    def test_parse_keys_missing_section(self):
        """Parse a keyfile missing a section."""
        keybindings = self.keybindings
        del keybindings["IMAGE"]
        keyfile = self.create_keyfile(keybindings)
        # Catch the sys.exit(1)
        with self.assertRaises(SystemExit):
            parser.parse_keys(keyfiles=[keyfile], running_tests=True)
        # pylint:disable=no-member
        output = sys.stdout.getvalue().strip()
        self.assertIn("Missing section", output)

    def test_parse_keys_no_keyfile(self):
        """Parse keybindings without any existing keyfiles."""
        keyfile = os.path.join(self.configdir, "nope_not_a_keyfile")
        # Catch the sys.exit(1)
        with self.assertRaises(SystemExit):
            parser.parse_keys(keyfiles=[keyfile], running_tests=True)
        # pylint:disable=no-member
        output = sys.stdout.getvalue().strip()
        self.assertIn("Keyfile not found", output)

    def test_parse_keys_duplicate(self):
        """Parse keybindings with a duplicate keybinding."""
        keybindings = self.keybindings
        keyfile = self.create_keyfile(keybindings)
        with open(keyfile, "a") as f:
            f.write("\na: scroll j")
        # Catch the sys.exit(1)
        with self.assertRaises(SystemExit):
            parser.parse_keys(keyfiles=[keyfile], running_tests=True)
        # pylint:disable=no-member
        output = sys.stdout.getvalue().strip()
        self.assertIn("Duplicate keybinding", output)

    @classmethod
    def create_configfile(cls, new_settings=None, text=None):
        """Create a vimiv configfile.

        Args:
            new_settings: Dictionary containing the settings for the configfile.
            text: Text to write to the configfile
        Return:
            path to the created configfile
        """
        configfile = os.path.join(cls.configdir,
                                  "vimivrc_" + str(cls.configfile_counter))
        cls.configfile_counter += 1
        if new_settings:
            general = new_settings["GENERAL"] \
                if "GENERAL" in new_settings.keys() \
                else {}
            library = new_settings["LIBRARY"] \
                if "LIBRARY" in new_settings.keys() \
                else {}
            aliases = new_settings["ALIASES"] \
                if "ALIASES" in new_settings.keys() \
                else {}
            with open(configfile, "w") as f:
                f.write("[GENERAL]\n")
                for setting in general.keys():
                    f.write("%s: %s\n" % (setting, general[setting]))
                f.write("[LIBRARY]\n")
                for setting in library.keys():
                    f.write("%s: %s\n" % (setting, library[setting]))
                f.write("[ALIASES]\n")
                for setting in aliases.keys():
                    f.write("%s: %s\n" % (setting, aliases[setting]))
        elif text:
            with open(configfile, "w") as f:
                f.write(text)

        return configfile
    def tearDown(self):
        """Rest all settings to default."""
        settings.reset()


    @classmethod
    def create_keyfile(cls, keybindings):
        """Create a vimiv keybinding file.

        Args:
            keybindings: Dictionary containing the keybindings for the file.
        Return:
            path to the created file
        """
        path = os.path.join(cls.configdir,
                            "keys.conf_" + str(cls.configfile_counter))
        keys = configparser.ConfigParser()
        for section in sorted(keybindings.keys()):
            keys[section] = keybindings[section]
        with open(path, "w") as keyfile:
            keys.write(keyfile)
        return path

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()


if __name__ == "__main__":
    main(buffer=True)
