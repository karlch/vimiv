#!/usr/bin/env python
# encoding: utf-8

import os
import shutil
from unittest import TestCase, main
import vimiv.helpers as helpers

class HelpersTest(TestCase):

    def setUp(self):
        os.mkdir("tmp_testdir")
        open("tmp_testdir/foo", "a").close()
        open("tmp_testdir/.foo", "a").close()

    def test_external_commands(self):
        external_commands = " ".join(list(helpers.external_commands))
        self.assertIn(" !ls ", external_commands)
        self.assertIn(" !pwd ", external_commands)

    def test_listdir_wrapper(self):
        no_hidden_files = helpers.listdir_wrapper("tmp_testdir", False)
        hidden_files = helpers.listdir_wrapper("tmp_testdir", True)
        self.assertEqual(len(no_hidden_files), 1)
        self.assertEqual(len(hidden_files), 2)
        self.assertEqual(hidden_files, sorted(hidden_files))

    def test_read_file(self):
        helpers.read_file("tmp_testdir/bar")
        self.assertTrue(os.path.exists("tmp_testdir/bar"))
        with open("tmp_testdir/baz", "w") as created_file:
            created_file.write("vimiv\nis\ngreat")
        created_file_content = helpers.read_file("tmp_testdir/baz")
        self.assertEqual(created_file_content, ["vimiv", "is", "great"])

    def tearDown(self):
        shutil.rmtree("tmp_testdir")

if __name__ == '__main__':
    main()
