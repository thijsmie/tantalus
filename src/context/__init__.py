from flask import current_app


def set_config(config):
    current_app.config['tantalus'] = config

def get_config():
    return current_app.config['tantalus']