import os
import sys

directory = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, directory)


from tantalus.appfactory.main import create_app
app, worker = create_app()
