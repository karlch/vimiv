# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Configparser Tests for vimiv's testsuite."""

import configparser
import os
import sys
import tempfile
from unittest import TestCase, main

import vimiv.configparser as parser


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

    def check_defaults(self, settings):
        """Check is settings contain default values."""
        defaults = parser.set_defaults()
        self.assertEqual(settings, defaults)

    def test_parse_config_empty(self):
        """Parse an empty configfile."""
        # Should set default values
        path = os.path.join(self.configdir, "empty_vimivrc")
        with open(path, "w") as f:
            f.write("")
        settings = parser.parse_config(path, True)
        self.check_defaults(settings)

    def test_unexisting_configfile(self):
        """Parse a non-existing configfile."""
        path = os.path.join(self.configdir, "this_file_does_not_exist")
        # Should ignore it and set default values
        settings = parser.parse_config(path, True)
        self.check_defaults(settings)

    def test_correct_configfile(self):
        """Parse correct non-default configfile with all settings."""
        settings = {"GENERAL": {"start_fullscreen": "yes",
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
        configfile = self.create_configfile(settings=settings)
        parsed_settings = parser.parse_config(configfile, True)
        # False positive
        # pylint: disable = unsubscriptable-object
        general = parsed_settings["GENERAL"]
        library = parsed_settings["LIBRARY"]
        aliases = parsed_settings["ALIASES"]
        self.assertEqual(general["start_fullscreen"], True)
        self.assertEqual(general["start_slideshow"], True)
        self.assertEqual(general["shuffle"], True)
        self.assertEqual(general["display_bar"], False)
        self.assertEqual(general["default_thumbsize"], (256, 256))
        self.assertEqual(general["geometry"], "400x400")
        self.assertEqual(general["recursive"], True)
        self.assertEqual(general["rescale_svg"], True)
        self.assertEqual(general["overzoom"], 1.5)
        self.assertEqual(general["search_case_sensitive"], True)
        self.assertEqual(general["incsearch"], False)
        self.assertEqual(general["copy_to_primary"], False)
        self.assertEqual(general["commandline_padding"], 0)
        self.assertEqual(general["completion_height"], 100)
        self.assertEqual(library["show_library"], True)
        self.assertEqual(library["library_width"], 200)
        self.assertEqual(library["expand_lib"], False)
        self.assertEqual(library["border_width"], 12)
        self.assertEqual(library["markup"], "<span foreground=\"#FF0000\">")
        self.assertEqual(library["show_hidden"], False)
        self.assertEqual(library["desktop_start_dir"],
                         os.path.expanduser("~/.local"))
        self.assertEqual(library["file_check_amount"], 10)
        self.assertEqual(library["tilde_in_statusbar"], False)
        self.assertIn("testalias", aliases.keys())
        self.assertEqual(aliases["testalias"], "zoom_in")

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

    def test_broken_settings(self):
        """Parse invalid values for settings."""
        def run_check(settings, expected_output):
            """Run check for settings, check for expected output."""
            configfile = self.create_configfile(settings=settings)
            parsed_settings = parser.parse_config(configfile,
                                                  running_tests=True)
            # pylint:disable=no-member
            output = sys.stdout.getvalue().strip()
            self.assertIn(expected_output, output)
            self.check_defaults(parsed_settings)
        # No value for setting
        settings = {"GENERAL": {"start_fullscreen": ""}}
        run_check(settings, "start_fullscreen")
        # Value is not an integer
        settings = {"GENERAL": {"slideshow_delay": "wrong"}}
        run_check(settings, "slideshow_delay")
        # Value is not a tuple
        settings = {"GENERAL": {"default_thumbsize": "wrong"}}
        run_check(settings, "default_thumbsize")
        # Invalid markup
        settings = {"LIBRARY": {"markup": "wrong"}}
        run_check(settings, "")
        # Directory does not exist
        settings = {"LIBRARY": {"desktop_start_dir": "~/foo/bar/baz/"}}
        run_check(settings, "")

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
    def create_configfile(cls, settings=None, text=None):
        """Create a vimiv configfile.

        Args:
            settings: Dictionary containing the settings for the configfile.
            text: Text to write to the configfile
        Return:
            path to the created configfile
        """
        configfile = os.path.join(cls.configdir,
                                  "vimivrc_" + str(cls.configfile_counter))
        cls.configfile_counter += 1
        if settings:
            general = settings["GENERAL"] \
                if "GENERAL" in settings.keys() \
                else {}
            library = settings["LIBRARY"] \
                if "LIBRARY" in settings.keys() \
                else {}
            aliases = settings["ALIASES"] \
                if "ALIASES" in settings.keys() \
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
