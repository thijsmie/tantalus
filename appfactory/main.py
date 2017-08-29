import os
import logging
from importlib import import_module

from flask import Flask, request, session, abort
from flask_bootstrap import Bootstrap

from api import tantalus
from auth import generate_random_string, auth
import paths


def create_app():
    app = Flask(__name__, template_folder=paths.TEMPLATE_FOLDER, static_folder=paths.STATIC_FOLDER)
    app.config["SECRET_KEY"] = "VERY_SECRET"
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

    # Setup CSRF-protection
    @app.before_request
    def csrf_protect():
        if request.method == "POST":
            if request.json and request.json.get('_csrf_token', ""):
                token = session.get('_csrf_token', None)
                if not token or token != request.json.get('_csrf_token'):
                    abort(403)
            elif request.form and request.form.get('_csrf_token', ""):
                token = session.get('_csrf_token', None)
                if not token or token != request.form.get('_csrf_token'):
                    abort(403)
            else:
                abort(403)

    def generate_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = generate_random_string(16)
        return session['_csrf_token']

    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    # Activate middleware.
    with app.app_context():
        import_module("appfactory.middleware")

    return app
