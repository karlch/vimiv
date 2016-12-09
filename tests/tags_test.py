#!/usr/bin/env python
# encoding: utf-8
"""Tag tests for vimiv's test suite."""

import os
from unittest import main
from vimiv.helpers import read_file
from vimiv_testcase import VimivTestCase


class TagsTest(VimivTestCase):
    """Tag Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def test_tag_create_remove(self):
        """Create and remove a tag."""
        taglist = ["vimiv/testimages/arch-logo.png",
                   "vimiv/testimages/arch_001.jpg"]
        taglist = [os.path.abspath(image) for image in taglist]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        created_file = os.path.expanduser("~/.vimiv/Tags/arch_test_tag")
        file_content = read_file(created_file)
        self.assertEqual(file_content, taglist)
        self.vimiv["tags"].remove("arch_test_tag")
        self.assertFalse(os.path.isfile(created_file))

    def test_tag_append(self):
        """Append to a tag."""
        taglist = [os.path.abspath("vimiv/testimages/arch-logo.png")]
        self.vimiv["tags"].write(taglist, "arch_test_tag")
        taglist2 = [os.path.abspath("vimiv/testimages/arch_001.jpg")]
        self.vimiv["tags"].write(taglist2, "arch_test_tag")
        complete_taglist = taglist + taglist2
        created_file = os.path.expanduser("~/.vimiv/Tags/arch_test_tag")
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
        self.assertEqual(self.vimiv.paths, taglist)
        self.vimiv["tags"].remove("arch_test_tag")

    def test_tag_errors(self):
        """Error messages with tags."""
        unavailable_file = os.path.expanduser("~/.vimiv/Tags/foo_is_real")
        if os.path.exists(unavailable_file):
            os.remove(unavailable_file)
        self.vimiv["tags"].load("foo_is_real")
        expected_text = "Tagfile 'foo_is_real' has no valid images"
        received_text = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_text, received_text)
        os.remove(unavailable_file)
        self.vimiv["tags"].remove("foo_is_real")  # Error message
        expected_text = "Tagfile 'foo_is_real' does not exist"
        received_text = self.vimiv["statusbar"].left_label.get_text()
        self.assertEqual(expected_text, received_text)

    def tearDown(self):
        os.chdir(self.working_directory)


if __name__ == '__main__':
    main()
