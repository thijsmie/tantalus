"""Convenience wrappers for flask.flash() with special-character handling.

With PyCharm inspections it's easy to see which custom flash messages are available. If you directly use flask.flash(),
the "type" of message (info, warning, etc.) is a string passed as a second argument to the function. With this file
PyCharm will tell you which type of messages are supported.
"""

from flask import flash


def default(message):
    return flash(message, 'default')


def success(message):
    return flash(message, 'success')


def info(message):
    return flash(message, 'info')


def warning(message):
    return flash(message, 'warning')


def danger(message):
    return flash(message, 'danger')


def well(message):
    return flash(message, 'well')


def modal(message):
    return flash(message, 'modal')
