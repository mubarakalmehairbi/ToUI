"""
Contains default functions that can be replaced by the user inside other modules.
"""


def validate_ws(ws):
    """The default function for validating `simple_websocket.ws.Server` object inside `Website`."""
    return True


def validate_data(data):
    """The default function for validating data received from JavaScript inside `Website`."""
    return True
