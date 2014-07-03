#!/usr/bin/env python

import ridewithgps
import latex
import tex

import cgi
import cgitb
import os
import sys

def dataExists(filename, base_dir):
  return os.path.isfile("%s/%s" % (base_dir, filename))

def servePDF(pdffilename):
  with open(pdffilename) as pdffile:
    sys.stdout.write("Content-type: application/pdf\r\n\r\n" + 
                     pdffile.read())

def htmlError(error_html):
  sys.stdout.write("Content-type: text/html\r\n\r\n"
                    + error_html.replace("\n", "<br>"))
      
cgitb.enable()
fields = cgi.FieldStorage()

if 'routeid' not in fields:
  htmlError("No route ID specified")
  sys.exit(1)

route_id = fields['routeid'].value
if not route_id.isalnum():
  htmlError("Invalid route id: " + cgi.escape(route_id))
  sys.exit(1)

md5_hash, cue_entries = ridewithgps.getMd5AndCueSheet(route_id)

basefilename = "%s-%s" % (route_id, md5_hash)
pdffilename  = basefilename + ".pdf"

# base_dir = "/mnt/shared/mucow_cgi/roboviva/"
base_dir = '.'
os.chdir(base_dir)

# Check if we've done this already:
if not dataExists(pdffilename, base_dir):
  latex = latex.makeLatex(cue_entries)
  try:
    with open(pdffilename, 'wb') as pdffile:
      pdffile.write(tex.latex2pdf(latex))
      sys.exit(0)
  except:
    htmlError("Error formatting latex!\n\n" + latex) 
    sys.exit(1)

servePDF(pdffilename)
