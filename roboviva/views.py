import flask
import flask.ext

import roboviva.ridewithgps
import roboviva.latex
import roboviva.tex

import os
import logging
import sys
import time

blueprint = flask.Blueprint("roboviva", __name__)


@blueprint.route('/routes/<int:route_id>')
def handle_request(route_id):
  log = flask.current_app.logger
  log.debug("[request][%10d]: start", route_id)

  # Step one - get cuesheet entries from ridewithgps
  # This is always necessary since the route might have changed since we last
  # processed it. We md5 the cue entries, and use that to see if it's worth
  # regenerating the PDF.
  try:
    md5_hash, cue_entries = roboviva.ridewithgps.getMd5AndCueSheet(route_id)
  except roboviva.ridewithgps.RideWithGpsError as e:
    log.warning("[request][%10d]: RideWithGPS error: %s", route_id, e)
    return flask.render_template('error.html', error=("'%s' is not a valid RideWithGPS Route :(" % route_id))
  except Exception as e:
    log.error("[request][%10d]: Other error: %s", route_id, e)
    return flask.render_template('error.html',
                                 error = 'Error querying RideWithGPS',
                                 meditation = '{Guru Meditation: 0xFA}')


  log.debug("[request][%10d]: GPS OK, md5 = %s", route_id, md5_hash)

  # Step two: Hash check
  # We use the flask shelve as a 'database', here, since it's easy and
  # performance isn't a major concern.
  # We map from str(route_id) -> (md5_hash, sec_since_epoch)
  hash_db = flask.ext.shelve.get_shelve('c')
  db_key  = str(route_id)
 
  is_present = db_key in hash_db
  old_hash   = None
  old_time   = None
  if is_present:
    old_hash, old_time = hash_db[db_key]

  if not is_present or old_hash != md5_hash:
    if not is_present:
      log.info("[request][%10d]: new_ent: %s", route_id, md5_hash)
    else:
      log.info("[request][%10d]: replace: %s -> %s", 
          route_id, old_hash, md5_hash)

    # Step three, make the latex:
    try:
      latex = roboviva.latex.makeLatex(cue_entries)
    except Exception as e:
      log.error("[request][%10d]: Error generating latex: %s\n cue:\n %s",
          route_id, e, cue_entries)
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
    hash_db[db_key] = (md5_hash, time.time())
  else:
    log.info("[request][%10d]:  cached: %s (%d sec ago)",
        route_id, md5_hash, time.time() - old_time)

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
  ret  = "<table border=1>\n"
  ret += "  <tr><th>route id</th><th>md5</th><th>age (s)</th></tr>\n"
  for k in hash_db:
    h, ts = hash_db[k]
    ret += "  <tr><td>%s</td><td>%s</td><td>%d</td></tr>\n" % (k, h, time.time() - ts)
  ret += "</table>\n"
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

