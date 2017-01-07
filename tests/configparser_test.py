#!/usr/bin/env python
# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Configparser Tests for vimiv's testsuite."""

import os
import shutil
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
        cls.tmpdir = tempfile.mkdtemp()
        os.mkdir("configfiles")
        cls.configfile_counter = 0  # Used to always create unique new filenames

    def test_parse_dirs(self):
        """Check if all directories where created correctly."""
        vimivdir = os.path.join(tempfile.mkdtemp() + "vimiv")
        parser.parse_dirs(vimivdir)
        trashdir = os.path.join(vimivdir, "Trash")
        tagdir = os.path.join(vimivdir, "Tags")
        thumbdir = os.path.join(vimivdir, "Thumbnails")
        for directory in [vimivdir, trashdir, tagdir, thumbdir]:
            with self.subTest(directory=directory):
                self.assertTrue(os.path.isdir(directory))

    def check_defaults(self, settings):
        """Check is settings contain default values."""
        general = settings["GENERAL"]
        library = settings["LIBRARY"]
        aliases = settings["ALIASES"]
        amount_general_settings = len(general.keys())
        amount_library_settings = len(library.keys())
        amount_aliases = len(aliases.keys())
        self.assertEqual(amount_general_settings, 18)
        self.assertEqual(amount_library_settings, 9)
        self.assertEqual(amount_aliases, 0)
        defaults = parser.set_defaults()
        self.assertEqual(settings, defaults)

    def test_parse_config_empty(self):
        """Parse an empty configfile."""
        # Should set default values
        settings = parser.parse_config("configfiles/empty_vimivrc")
        self.check_defaults(settings)

    def test_unexisting_configfile(self):
        """Parse a non-existing configfile."""
        # Should ignore it and set default values
        settings = parser.parse_config("configfiles/this_file_does_not_exist")
        self.check_defaults(settings)

    def test_correct_configfile(self):
        """Parse correct non-default configfile with all settings."""
        settings = {"GENERAL": {"start_fullscreen": "yes",
                                "start_slideshow": "yes",
                                "shuffle": "yes",
                                "display_bar": "no",
                                "thumbsize": "(100, 100)",
                                "thumb_maxsize": "(200, 200)",
                                "geometry": "400x400",
                                "recursive": "yes",
                                "rescale_svg": "yes",
                                "overzoom": "yes",
                                "search_case_sensitive": "yes",
                                "incsearch": "no",
                                "cache_thumbnails": "yes",
                                "copy_to_primary": "no",
                                "commandline_padding": 0,
                                "completion_height": 100},
                    "LIBRARY": {"show_library": "yes",
                                "library_width": "200",
                                "expand_lib": "no",
                                "border_width": "12",
                                "markup": "<span foreground=\"#FF0000\">",
                                "show_hidden": "no",
                                "desktop_start_dir": "~/.vimiv",
                                "file_check_amount": "10",
                                "tilde_in_statusbar": "no"},
                    "ALIASES": {"testalias": "zoom_in"}}
        configfile = self.create_configfile(settings=settings)
        parsed_settings = parser.parse_config(configfile)
        general = parsed_settings["GENERAL"]
        library = parsed_settings["LIBRARY"]
        aliases = parsed_settings["ALIASES"]
        self.assertEqual(general["start_fullscreen"], True)
        self.assertEqual(general["start_slideshow"], True)
        self.assertEqual(general["shuffle"], True)
        self.assertEqual(general["display_bar"], False)
        self.assertEqual(general["thumbsize"], (100, 100))
        self.assertEqual(general["thumb_maxsize"], (200, 200))
        self.assertEqual(general["geometry"], "400x400")
        self.assertEqual(general["recursive"], True)
        self.assertEqual(general["rescale_svg"], True)
        self.assertEqual(general["overzoom"], True)
        self.assertEqual(general["search_case_sensitive"], True)
        self.assertEqual(general["incsearch"], False)
        self.assertEqual(general["cache_thumbnails"], True)
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
                         os.path.expanduser("~/.vimiv"))
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
        settings = {"GENERAL": {"thumbsize": "wrong"}}
        run_check(settings, "thumbsize")
        # Invalid markup
        settings = {"LIBRARY": {"markup": "wrong"}}
        run_check(settings, "")
        # Directory does not exist
        settings = {"LIBRARY": {"desktop_start_dir": "~/foo/bar/baz/"}}
        run_check(settings, "")

    def test_parse_keys(self):
        """Check if the keybindings are parsed correctly."""
        keybindings = parser.parse_keys()
        image_bindings = keybindings["IMAGE"]
        self.assertEqual(image_bindings["j"], "scroll j")

    @classmethod
    def create_configfile(cls, settings=None, text=None):
        """Create a vimiv configfile.

        Args:
            settings: Dictionary containing the settings for the configfile.
            text: Text to write to the configfile
        Return:
            path to the created configfile
        """
        configfile = "configfiles/vimivrc_" + str(cls.configfile_counter)
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
    def tearDownClass(cls):
        shutil.rmtree("configfiles")
        shutil.rmtree(cls.tmpdir)


if __name__ == '__main__':
    main(buffer=True)
