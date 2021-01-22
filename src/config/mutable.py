from flask import g
from werkzeug.local import LocalProxy

from tantalus_db.base import db
from tantalus_db.config import Setting


class Config:
    def __init__(self):
        settings = {s.name: s.value for s in Setting.query.all()}
        if not settings:
            default_configure()
            settings = {s.name: s.value for s in Setting.query.all()}

        for setting, value in settings.items():
            setattr(self, setting, value)


def get_config():
    if 'application_config' not in g:
        g.application_config = Config()

    return g.application_config

config = LocalProxy(get_config)
        

def default_configure():
    settings = [
        ("smtp_host", "", True),
        ("smtp_port", "", True),
        ("smtp_user", "", True),
        ("smtp_pass", "", True),
        ("smtp_sender", "", True),
        ("conscribo_api_url", "", True),
        ("conscribo_api_key", "", True),
        ("conscribo_api_secret", "", True),
        ("yearcode", "2021", False),
        ("nologin", "false", False)
    ]

    for name, value, secret in settings:
        s = Setting(name=name, value=value, secret=secret)
        db.session.add(s)
    db.session.commit()