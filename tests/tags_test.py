# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Tag tests for vimiv's test suite."""

import os
from unittest import main

from gi import require_version
require_version('Gtk', '3.0')
from vimiv.helpers import read_file, get_user_data_dir

from vimiv_testcase import VimivTestCase


class TagsTest(VimivTestCase):
    """Tag Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)
        cls.tagdir = os.path.join(get_user_data_dir(), "vimiv", "Tags")

    def test_tag_create_remove(self):
        """Create and remove a tag."""
        taglist = ["vimiv/testimages/arch-logo.png",
                   "vimiv/testimages/arch_001.jpg"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        created_file = os.path.join(self.tagdir, "arch_test_tag")
        file_content = read_file(created_file)
        self.assertEqual(file_content, taglist)
        self.vimiv["tags"].remove("arch_test_tag")
        self.assertFalse(os.path.isfile(created_file))

    def test_tag_create_remove_with_whitespace(self):
        """Create and remove a tag with whitespace in the name."""
        taglist = ["vimiv/testimages/arch-logo.png",
                   "vimiv/testimages/arch_001.jpg"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["tags"].write(taglist, "arch test tag")
        created_file = os.path.join(self.tagdir, "arch test tag")
        file_content = read_file(created_file)
        self.assertEqual(file_content, taglist)
        self.vimiv["tags"].remove("arch test tag")
        self.assertFalse(os.path.isfile(created_file))

    def test_tag_append(self):
        """Append to a tag."""
        taglist = [os.path.abspath("vimiv/testimages/arch-logo.png")]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        taglist2 = [os.path.abspath("vimiv/testimages/arch_001.jpg")]
        self.vimiv["tags"].write(taglist2, "arch_test_tag")
        complete_taglist = taglist + taglist2
        created_file = os.path.join(self.tagdir, "arch_test_tag")
        file_content = read_file(created_file)
        self.assertEqual(file_content, complete_taglist)
        self.vimiv["tags"].remove("arch_test_tag")

    def test_tag_load(self):
        """Load a tag."""
        taglist = ["vimiv/testimages/arch-logo.png",
                   "vimiv/testimages/arch_001.jpg"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        self.vimiv["tags"].load("arch_test_tag")
        self.assertEqual(self.vimiv.get_paths(), taglist)
        self.vimiv["tags"].remove("arch_test_tag")

    def test_tag_load_single(self):
        """Load a tag with only one file."""
        taglist = ["vimiv/testimages/arch-logo.png"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        self.vimiv["tags"].load("arch_test_tag")
        self.assertEqual(self.vimiv.get_paths(), taglist)
        self.vimiv["tags"].remove("arch_test_tag")

    def test_tag_errors(self):
        """Error messages with tags."""
        unavailable_file = os.path.join(self.tagdir, "foo_is_real")
        self.vimiv["tags"].load("foo_is_real")
        self.check_statusbar("ERROR: Tagfile 'foo_is_real' has no valid images")
        os.remove(unavailable_file)
        self.vimiv["tags"].remove("foo_is_real")  # Error message
        self.check_statusbar("ERROR: Tagfile 'foo_is_real' does not exist")

    def test_tag_commandline(self):
        """Tag commands from command line."""
        # Set some marked images
        taglist = ["vimiv/testimages/arch-logo.png",
                   "vimiv/testimages/arch_001.jpg"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["mark"].marked = list(taglist)
        # Write a tag
        self.run_command("tag_write new_test_tag")
        created_file = os.path.join(self.tagdir, "new_test_tag")
        file_content = read_file(created_file)
        self.assertEqual(taglist, file_content)
        # Load a tag
        self.run_command("tag_load new_test_tag")
        self.assertEqual(self.vimiv.get_paths(), taglist)
        # Delete a tag
        self.run_command("tag_remove new_test_tag")
        self.assertFalse(os.path.isfile(created_file))

    def tearDown(self):
        os.chdir(self.working_directory)


if __name__ == "__main__":
    main()
