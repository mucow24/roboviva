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

import flask
import flask.ext

import roboviva.ridewithgps
import roboviva.latex
import roboviva.tex

import os
import logging
import sys
import time

blueprint = flask.Blueprint("roboviva", __name__, static_folder='static', static_url_path="")

@blueprint.route('/')
def index():
  return flask.current_app.send_static_file('index.html')

@blueprint.route('/routes/<int:route_id>')
def handle_request(route_id):
  log = flask.current_app.logger
  log.debug("[request][%10d]: start", route_id)

  # Roboviva uses the HTTP ETag header to determine if it's worth
  # re-downloading the route information from RideWithGPS, so step one is
  # determining if we have an ETag already on hand:
  hash_db = flask.ext.shelve.get_shelve('c')
  db_key  = str(route_id)
  cached_etag = None
  if db_key in hash_db:
    cached_etag = hash_db[db_key]

  # Query RideWithGPS. This method will return the current ETag, and, if the
  # current ETag is different from the one we have on file, the full cue data
  # for the route:
  try:
    cur_etag, cur_route = roboviva.ridewithgps.getETagAndCuesheet_viaCSV(route_id, cached_etag)
  except roboviva.ridewithgps.RideWithGpsError as e:
    log.warning("[request][%10d]: RideWithGPS error: %s", route_id, e)
    return flask.render_template('error.html', error=("'%s' is not a valid RideWithGPS Route :(" % route_id))
  except Exception as e:
    log.error("[request][%10d]: Other error: %s", route_id, e)
    return flask.render_template('error.html',
                                 error = 'Error querying RideWithGPS',
                                 meditation = '{Guru Meditation: 0xFA}')

  log.debug("[request][%10d]: GPS OK, old etag: %s cur etag:", route_id, cached_etag, cur_etag)

  if cur_etag == cached_etag:
    log.info("[request][%10d]: No changes, redirecting to cache.")
  else:
    # Need to update the cache, and regenerate the PDF:
    if cached_etag is None:
      log.info("[request][%10d]: new_ent: %s", route_id, cur_etag)
    else:
      log.info("[request][%10d]: replace: %s -> %s",
               route_id, cached_etag, cur_etag)

    # Step three, make the latex:
    try:
      latex = roboviva.latex.makeLatex(cur_route)
    except Exception as e:
      log.error("[request][%10d]: Error generating latex: %s\n cue:\n %s",
          route_id, e, cur_route)
      return flask.render_template('error.html',
                                   error = "Internal Error :(",
                                   meditation = "{Guru Meditation: 0xBA - Cue Parsing Failed}")

    # Step four, render the pdf:
    try:
      pdf_data = roboviva.tex.latex2pdf(latex)
    except Exception as e:
      log.error("[request][%10d]: Error generating PDF\n latex: \n %s\n error:\n%s",
          route_id, latex, e)
      return flask.render_template(
          'error.html',
          error = "Internal Error :(",
          meditation = "{Guru Meditation: 0xFF - Error Rendering PDF}")

    # Step five, write it:
    cache_dir = flask.current_app.config['PDF_CACHE_DIR']
    pdf_filename = "%s.pdf" % (route_id)
    pdf_filepath = os.path.join(cache_dir, pdf_filename)
    try:
      with open(pdf_filepath, 'wb') as pdffile:
        pdffile.write(roboviva.tex.latex2pdf(latex))
    except Exception as e:
      log.error("[request][%10d]: Error writing pdf to %s: %s", route_id, pdf_filepath, e)
      return flask.render_template(
          'error.html',
          error = "Internal Error :(",
          meditation = "{Guru Meditation: 0xCE - Error writing PDF}")

    # Update the hash db:
    hash_db[db_key] = (cur_etag, time.time())

  # ...and point them to the final PDF, which can be served statically from
  # pdfs/<route_id>.pdf:
  return flask.redirect(flask.url_for('roboviva.get_pdf',
                                      route_id   = route_id))

@blueprint.route('/pdfs/<int:route_id>.pdf')
def get_pdf(route_id):
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']
  pdf_filename = "%s.pdf" % (route_id)
  pdf_filepath = os.path.join(cache_dir, pdf_filename)
  if not os.path.exists(pdf_filepath):
    return flask.render_template('regen.html', route_id = route_id)
  return flask.send_from_directory(
      cache_dir,
      pdf_filename,
      mimetype = "application/pdf",
      as_attachment = False)

@blueprint.route('/cache')
def dump_cache():
  hash_db = flask.ext.shelve.get_shelve('c')
  ents = []
  for route_id in hash_db:
    md5_sum, ts = hash_db[route_id]
    ents.append( (ts, route_id, md5_sum) )

  ret  = "<table border=1>\n"
  ret += "  <tr><th>route id</th><th>md5</th><th>age</th><th>Remove?</th></tr>\n"
  for timestamp, route_id, md5_sum in sorted(ents):
    ret += "  <tr>\n"
    ret += "    <td>%s</td>\n" % route_id
    ret += "    <td>%s</td>\n" % md5_sum
    age = time.time() - timestamp
    age_str = ""
    if age < 60:
      age_str = "%d sec" % age
    elif age > 60 and age < 3600:
      age_str = "%d min" % (age / 60.)
    elif age > 3600 and age < 86400:
      age_str = "%d hr" % (age / 3600.)
    else:
      age_str = "%.1f days" % (age / 86400.)
    ret += "    <td>%s</td>\n" % age_str
    ret += "    <td><a href=%s>Remove</a></td>\n" % (flask.url_for('roboviva.remove_route',
                                                                    route_id = route_id))
    ret += "  </tr>\n"
  ret += "</table>\n"
  return ret

@blueprint.route('/cache/remove/<int:route_id>')
def remove_route(route_id):
  hash_db = flask.ext.shelve.get_shelve('c')
  ret = ""
  db_key = str(route_id)
  if db_key in hash_db:
    del hash_db[db_key]
    ret = "%s removed from cache" % route_id
  else:
    ret = "%s not found in cache" % route_id
  return ret

@blueprint.route('/cache/purge/<int:delete_older_than>')
def purge_cache(delete_older_than):
  log = flask.current_app.logger
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']
  hash_db = flask.ext.shelve.get_shelve('c')
  log.warning("[purge] starting: age: %s", delete_older_than)
  bytes_deleted   = 0
  bytes_remaining = 0
  ret  = "<table border=1>\n"
  ret += "  <tr><th>route id</th><th>md5</th><th>age (s)</th><th>status</th></tr>\n"
  for route_id in hash_db:
    h, ts = hash_db[route_id]
    pdf_filename = "%s.pdf" % (route_id)
    pdf_filepath = os.path.join(cache_dir, pdf_filename)
    status = ""
    if (time.time() - ts > delete_older_than):
      log.warning("[purge]: Nuking %s (%d sec old): %s",
          route_id, time.time() - ts, pdf_filepath)
      try:
        file_size = os.stat(pdf_filepath).st_size
        os.unlink(pdf_filepath)
        bytes_deleted += file_size
        status = "DELETED"
      except Exception as e:
        log.error("[purge]: Error unlinking %s: %s", pdf_filepath, e)
        status = "ERROR"
      del hash_db[route_id]
    else:
      file_size = os.stat(pdf_filepath).st_size
      bytes_remaining += file_size
    ret += "  <tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>\n" % \
        (route_id, h, time.time() - ts, status)
  ret += "</table>\n"
  ret += "%d kB deleted, %d kB remaining" % (bytes_deleted / 1024, bytes_remaining / 1024)
  return ret

