"""

All variables that are static for deployment come from environment variables. This means you can supply them easily with a .env file.
All mutable variables should be supplied using the DB.

"""
import os
import json


def config_loader(prefix):
    data = {}
    for var in os.environ:
        if var.startswith(prefix):
            key = var[len(prefix):]
            value = os.environ[var]

            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
            
            data[key] = value
    return data


def get_flask_config():
    """ All Flask Config should be prefixed with FL_ """
    return config_loader("FL_")
