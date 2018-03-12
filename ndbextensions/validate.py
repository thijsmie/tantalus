from google.appengine.ext.db import BadValueError


class ValidationError(BadValueError):
    def __init__(self, prop, msg):
        self.message = str(prop._name) + ": " + msg


class OperationError(BadValueError):
    def __init__(self, msg):
        self.message = msg


def ensurelength(length):
    def validator(prop, value):
        if len(value) < length:
            raise ValidationError(prop, "Minimum length is {}".format(length))
        return value

    return validator


def ensurepositive():
    def validator(prop, value):
        if value < 0:
            raise ValidationError(prop, "Should be positive.")
        return value

    return validator


def ensureexists():
    def validator(prop, value):
        if value.get() is None:
            raise ValueError(prop, "Entry of type {} with id {} does not exist.".format(value.kind(), value.urlsafe()))
        return value

    return validator


def combine(*args):
    def validator(prop, value):
        v = value
        for a in args:
            v = a(prop, v)

    return validator
