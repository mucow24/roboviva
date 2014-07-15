from flask import Flask
from flask.ext import shelve
from .views import blueprint

import sys
reload(sys)
sys.setdefaultencoding("utf8")

app = Flask(__name__)
app.config.from_object('config')
app.register_blueprint(blueprint, url_prefix="/roboviva")
shelve.init_app(app)
