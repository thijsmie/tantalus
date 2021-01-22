import logging
from importlib import import_module

from flask import Flask
from flask_bootstrap import Bootstrap

from config import get_flask_config, get_celery_config

from tantalus_db.base import db
import tantalus_db.models
import tantalus_db.conscribo
import tantalus_db.snapshot

from tantalus.api.routers import blueprints, activate_routes
from worker.worker import celery

from .auth import auth
import tantalus.appfactory.paths as paths

from celery import Task


def create_app():
    app = Flask(__name__, template_folder=paths.TEMPLATE_FOLDER, static_folder=paths.STATIC_FOLDER)

    app.config.update(get_flask_config())
    celery.conf.update(get_celery_config())

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

    activate_routes()
    for bp in blueprints:
        app.register_blueprint(bp)

    # Activate middleware.
    with app.app_context():
        import_module("tantalus.appfactory.middleware")

    return app, celery
