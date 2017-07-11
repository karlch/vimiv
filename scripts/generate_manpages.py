# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Generates vimiv's man pages from the markdown pages of the website.

Note: This scripts uses the directory of the website which is defined just after
the imports. Adapt this to your own usage.
"""

import os
import re
import shutil
import sys

website_directory = os.path.expanduser("~/Coding/git/vimiv/vimiv-website/")


def get_markdown_files(source="_pages/docs/", target="man/"):
    """Copy markdown files from source to target."""
    os.makedirs(target, exist_ok=True)
    source_include = os.path.join(source, "include")
    for f in ["manpage.md", "manpage_5.md"]:
        shutil.copyfile(os.path.join(source, f), os.path.join(target, f))
    if os.path.isdir(os.path.join(target, "include")):
        shutil.rmtree(os.path.join(target, "include"))
    shutil.copytree(source_include, os.path.join(target, "include"), )


def delete_jekyll_header(source):
    """Delete the --- whatever --- jekyll header from source."""
    with open(source) as f:
        lines = f.readlines()

    amount = 0
    while amount != 2:
        line = lines[0]
        if "---" in line:
            amount += 1
        del lines[0]

    with open(source, "w") as f:
        for line in lines:
            f.write(line)


def strip_html(source):
    """Remove all html tags from source."""
    clean_html = re.compile('<.*?>')

    with open(source) as f:
        content = f.read()
    cleaned_content = re.sub(clean_html, "", content)

    with open(source, "w") as f:
        f.write(cleaned_content)


def escape_markdown_characters(source):
    """Escape special markdown characters like "^" in source."""
    with open(source) as f:
        content = f.read()
    cleaned_content = content.replace("^", "\^")

    with open(source, "w") as f:
        f.write(cleaned_content)


def generate_main_page(source="man/manpage.md", target="man/vimiv.1"):
    """Generate the main vimiv man page from source markdown to target."""
    delete_jekyll_header(source)
    escape_markdown_characters(source)
    cmd = "md2man-roff %s > %s" % (source, target)
    os.system(cmd)


def replace_include_lines(source):
    """Replace jekyll include lines with the actual markdown content."""
    with open(source) as f:
        lines = f.readlines()

    workcopy = list(lines)
    for i, line in enumerate(workcopy):
        dirname = os.path.dirname(source)
        if "include_relative" in line:
            basename = line.split()[2]
            filename = os.path.join(dirname, basename)
            with open(filename) as f:
                content = f.read()
            lines[i] = content

    with open(source, "w") as f:
        for line in lines:
            f.write(line)


def convert_tables(source):
    """Convert markdown tables from source into a nicer format for man."""
    with open(source) as f:
        lines = f.readlines()

    workcopy = list(lines)
    for i, line in enumerate(workcopy):
        # Table
        if line.startswith("|"):
            # Separator
            if line[2] == "-" or "|Setting|" in line or "|Name|" in line:
                lines[i] = ""
            # Content of a table  line
            else:
                content = line.split("|")
                try:
                    setting = content[1]
                    value = content[2]
                    description = content[4]
                    new = "`%s`, `%s`\n  %s\n\n" % (setting, value, description)
                # Table is shorter, use different format
                except IndexError:
                    name = content[1]
                    description = content[2]
                    new = "`%s`\n  %s\n\n" % (name, description)
                lines[i] = new

        with open(source, "w") as f:
            # pylint: disable=redefined-outer-name
            # We only use line in the loops anyway
            for line in lines:
                f.write(line)


def generate_config_page(source="man/manpage_5.md", target="man/vimiv.5"):
    """Generate the vimivrc man page from source markdown to target."""
    delete_jekyll_header(source)
    replace_include_lines(source)
    convert_tables(source)
    strip_html(source)
    escape_markdown_characters(source)
    cmd = "md2man-roff %s > %s" % (source, target)
    os.system(cmd)


if __name__ == "__main__":
    # Move to website directory
    try:
        working_directory = os.getcwd()
        os.chdir(website_directory)
    except FileNotFoundError as e:
        print("Website directory not found.")
        print(e)
        sys.exit(1)
    get_markdown_files()
    generate_main_page(target=os.path.join(working_directory, "man", "vimiv.1"))
    generate_config_page(target=os.path.join(working_directory, "man",
                                             "vimivrc.5"))
