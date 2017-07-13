# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Contains custom exceptions used by vimiv."""


class NoSearchResultsError(Exception):
    """Raised when a search result is accessed although there are no results."""


class StringConversionError(ValueError):
    """Raised when a setting or argument could not be converted to its type."""


class SettingNotFoundError(Exception):
    """Raised when a setting does not exist."""


class NotABoolean(Exception):
    """Raised when a setting is not a boolean."""


class NotANumber(Exception):
    """Raised when a setting is not a number."""


class AliasError(Exception):
    """Raised when there are problems when adding an alias."""


class TrashUndeleteError(Exception):
    """Raised when there were problems calling :undelete."""


class NotTransformable(Exception):
    """Raised when an image is not transformable for transform.py."""
