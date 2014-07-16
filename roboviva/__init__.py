from flask import Flask
from flask.ext import shelve
from .views import blueprint

import sys
import logging

# Get ourselves into utf8 mode, so we don't have ascii / unicode headaches:
reload(sys)
sys.setdefaultencoding("utf8")

app = Flask(__name__, static_url_path='')
app.config.from_object('config')
app.register_blueprint(blueprint,
                       url_prefix="/roboviva")

if not app.debug:
  # In production mode, add log handler to sys.stderr.
  app.logger.addHandler(logging.StreamHandler())
  app.logger.setLevel(logging.WARN)

shelve.init_app(app)
