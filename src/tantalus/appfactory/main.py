import logging
from importlib import import_module

from flask import Flask
from flask_bootstrap import Bootstrap

from context import set_config

from tantalus_db.base import db
import tantalus_db.models
import tantalus_db.conscribo
import tantalus_db.snapshot

from tantalus.api import routers
from worker.worker import celery

from .auth import auth
import tantalus.appfactory.paths as paths

from celery import Task


def create_app(config, create_db=False):
    app = Flask(__name__, template_folder=paths.TEMPLATE_FOLDER, static_folder=paths.STATIC_FOLDER)
    app.config.update(**config.flask.dict)
    celery.conf.update(**config.celery.dict)

    class ContextTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.test_request_context():
                res = self.run(*args, **kwargs)
                return res

    celery.Task = ContextTask
    celery.finalize()

    Bootstrap(app)
    auth.init_app(app)
    db.init_app(app)

    app.add_url_rule('/favicon.ico', 'favicon', lambda: app.send_static_file('favicon.ico'))
    for bp in routers.blueprints:
        app.register_blueprint(bp)

    # Logging, remove in production
    @app.before_request
    def enable_local_error_handling():
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)

    # Activate middleware.
    with app.app_context():
        import_module("tantalus.appfactory.middleware")
        set_config(config)
        if create_db:
            db.create_all()

    return app, celery
