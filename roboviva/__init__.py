# Roboviva - Better cue sheets for everyone
# Copyright (C) 2015 Mike Kocurek
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
