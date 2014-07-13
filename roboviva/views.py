import flask

import roboviva.ridewithgps
import roboviva.latex
import roboviva.tex

import os
import sys

blueprint = flask.Blueprint("roboviva", __name__)

@blueprint.route('/routes/<int:route_id>')
def handle_request(route_id):
  print "route_id: %s" % route_id
  try:
    md5_hash, cue_entries = roboviva.ridewithgps.getMd5AndCueSheet(route_id)
  except:
    print "bad route"
    return "Bad route: %s" % route_id

  print "good route" 
  # check the pdf cache to see if we already have this:
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']

  # We want to use the 'int' url parser, so convert the md5 to base-10:
  md5_hash = int(md5_hash, 16)

  pdf_filename = "%s-%s.pdf" % (route_id, md5_hash)
  pdf_filepath = os.path.join(cache_dir, pdf_filename)
  if not os.path.exists(pdf_filepath):
    try:
      latex = roboviva.latex.makeLatex(cue_entries)
    except Exception as e:
      return "Error generating latex: %s\n entries:\n %s" % (e, cue_entries)

    try:
      with open(pdf_filepath, 'wb') as pdffile:
        pdffile.write(roboviva.tex.latex2pdf(latex))
    except Exception as e:
      return "Error writing to %s: %s\n Latex:\n %s" % (pdf_filepath, e, latex)
  return flask.redirect(flask.url_for('roboviva.get_pdf',
                                      route_id   = route_id,
                                      md5_as_int = md5_hash))

@blueprint.route('/pdfs/<int:route_id>/<int:md5_as_int>')
def get_pdf(route_id, md5_as_int):
  cache_dir = flask.current_app.config['PDF_CACHE_DIR']
  pdf_filename = "%s-%s.pdf" % (route_id, md5_as_int)
  return flask.send_from_directory(
      cache_dir,
      pdf_filename,
      mimetype = "application/pdf",
      as_attachment = True,
      attachment_filename = str(route_id) + ".pdf")
