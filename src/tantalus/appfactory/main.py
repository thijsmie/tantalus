import logging
from importlib import import_module

from flask import Flask
from flask_bootstrap import Bootstrap

from context import set_config

from tantalus.api import routes
from worker.worker import celery
from tantalus_db.base import db

from .auth import auth
import .paths


def create_app(config):
    app = Flask(__name__, template_folder=paths.TEMPLATE_FOLDER, static_folder=paths.STATIC_FOLDER)
    app.config.update(**config.flask.config)
    celery.conf.update(**config.celery.config)

    Bootstrap(app)
    auth.init_app(app)
    db.init_app(app)

    app.add_url_rule('/favicon.ico', 'favicon', lambda: app.send_static_file('favicon.ico'))
    for bp in tantalus.blueprints:
        app.register_blueprint(bp)

    # Logging, remove in production
    @app.before_request
    def enable_local_error_handling():
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)

    # Activate middleware.
    with app.app_context():
        import_module("appfactory.middleware")
        set_config(config)

    return app, celery
