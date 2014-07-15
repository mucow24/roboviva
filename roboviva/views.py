import flask
import flask.ext

import roboviva.ridewithgps
import roboviva.latex
import roboviva.tex

import os

blueprint = flask.Blueprint("roboviva", __name__)

@blueprint.route('/routes/<int:route_id>')
def handle_request(route_id):
  print route_id
  md5_hash, cue_entries = roboviva.ridewithgps.getMd5AndCueSheet(route_id)
  
  # check the pdf cache to see if we already have this:
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']
  
  hash_db = flask.ext.shelve.get_shelve('c')
  db_key  = str(route_id)
  if not db_key in hash_db or hash_db[db_key] != md5_hash:
    if db_key in hash_db:
      print "%s : present: old: %s new: %s" % (route_id, hash_db[db_key], md5_hash)
    else:
      print "%s : new_ent: %s" % (route_id, hash_db[db_key], md5_hash)

    pdf_filename = "%s.pdf" % (route_id)
    pdf_filepath = os.path.join(cache_dir, pdf_filename)
    latex = roboviva.latex.makeLatex(cue_entries)
    with open(pdf_filepath, 'wb') as pdffile:
      pdffile.write(roboviva.tex.latex2pdf(latex))
    hash_db[db_key] = md5_hash
  else:
    print "%s : hashed: %s" % (route_id, md5_hash)
  return flask.redirect(flask.url_for('roboviva.get_pdf',
                                      route_id   = route_id))

@blueprint.route('/pdfs/<int:route_id>.pdf')
def get_pdf(route_id):
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']
  pdf_filename = "%s.pdf" % (route_id)
  return flask.send_from_directory(
      cache_dir,
      pdf_filename,
      mimetype = "application/pdf",
      as_attachment = False)
