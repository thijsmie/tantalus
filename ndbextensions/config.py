from google.appengine.ext import ndb
from appfactory.auth import generate_random_string


class Config(ndb.Model):
    flask_secret_key = ndb.StringProperty(default=generate_random_string(100))

    @classmethod
    def get_config(cls):
        return cls.get_or_insert("MAIN")