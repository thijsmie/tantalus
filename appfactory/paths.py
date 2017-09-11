"""Make paths importable app-wide"""

import os

import entrypoint as app_root

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
API_FOLDER = os.path.join(APP_ROOT_FOLDER, 'api')
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')
VALIDATOR_FOLDER = os.path.join(APP_ROOT_FOLDER, 'validators')
