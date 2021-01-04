import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, directory)


from config import Config
from tantalus.appfactory.main import create_app

config = Config(filename=os.path.join(directory, "config.json"))
flask, celery = create_app(config)

app = flask