from google.appengine.ext import ndb
from appfactory.auth import generate_random_string


class Config(ndb.Model):
    flask_secret_key = ndb.StringProperty(default=generate_random_string(100))
    conscribo_api_url = ndb.StringProperty(default="")
    conscribo_api_key = ndb.StringProperty(default="")
    conscribo_api_secret = ndb.StringProperty(default="")
    conscribo_todo_account = ndb.IntegerProperty(default=999)
    yearcode = ndb.IntegerProperty(default=2021)

    @classmethod
    def get_config(cls):
        return cls.get_or_insert("MAIN")