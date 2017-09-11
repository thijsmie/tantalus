import logging
from importlib import import_module

from flask import Flask
from flask_bootstrap import Bootstrap

from api import tantalus
from auth import auth
import paths
from ndbextensions.config import Config


def create_app():
    app = Flask(__name__, template_folder=paths.TEMPLATE_FOLDER, static_folder=paths.STATIC_FOLDER)
    config = Config.get_config()
    app.config["SECRET_KEY"] = config.flask_secret_key

    Bootstrap(app)
    auth.init_app(app)

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

    return app
