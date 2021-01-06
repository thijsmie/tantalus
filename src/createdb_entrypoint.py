import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, directory)


from config import Config
from tantalus.appfactory.main import create_app
import logging
logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

config = Config(filename=os.path.join(directory, "config.json"))
create_app(config, True)
