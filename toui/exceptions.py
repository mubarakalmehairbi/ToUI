"""
A module that contains exceptions.
"""

class ToUIWrongPlaceException(Exception):
    """Raised when the user calls a function in the wrong place."""


class ToUINotAddedError(Exception):
    """Raised when the user calls a function which requires an extension that is not yet added to the app."""


class ToUIOverlapException(Exception):
    """Raised when the user calls two methods or callables that cannot exist together."""
    