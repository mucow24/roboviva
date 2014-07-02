#!/usr/bin/env python

import cgi
import cgitb
import csv
import cue
import os
import shutil
import subprocess
import sys
import tempfile
import urllib2
import hashlib

def getCsvData(route_id):
  url = 'http://ridewithgps.com/routes/%s.csv' % route_id
  csv_data = []
  try:
    csv_data = urllib2.urlopen(url).read()
    return (hashlib.md5(csv_data).hexdigest(), csv_data)
  except:
    print "Content-type: text/html"
    print
    print "<H1>Robo-Error: Invalid route ID: %s</H1>" % route_id
    sys.exit(0)


def makeLatex(processed_rows):
  latex = cue.LatexHeader
  for row in csv_rows:
    latex = latex + cue.formatRow(row) + "\n"
  latex = latex + cue.LatexFooter
  return latex

def dataExists(filename, base_dir="/mnt/shared/mucow_cgi/roboviva"):
  return os.path.isfile("%s/%s" % (base_dir, filename))

def servePDF(filename):
  sys.stdout.write( "Content-type: application/pdf\r\n\r\n" + file(filename,"rb").read() )
      
cgitb.enable()
fields = cgi.FieldStorage()

if 'routeid' not in fields:
  raise Error("No route ID specified")



route_id = fields['routeid'].value
if not route_id.isalnum():
  raise Error("Invalid route id: " + cgi.escape(route_id))

md5_hash, csv_data = getCsvData(route_id)

basefilename = "%s-%s" % (route_id, md5_hash)
texfilename  = basefilename + ".tex"
pdffilename  = basefilename + ".pdf"
auxfilename  = basefilename + ".aux"
logfilename  = basefilename + ".log"

base_dir = "/mnt/shared/mucow_cgi/roboviva/"
os.chdir(base_dir)

# Check if we've done this already:
if dataExists(pdffilename):
  servePDF(pdffilename)
  sys.exit(0)

csv_rows = cue.processRows(csv_data.split('\n'))
latex    = makeLatex(csv_rows)
latexfile = open(texfilename, 'w')
latexfile.write(latex)
latexfile.close()

try:
  p = subprocess.Popen(["/usr/bin/pdflatex", "-interaction=nonstopmode", texfilename], stdout=subprocess.PIPE)
  stdout, stderr = p.communicate()
  if os.path.isfile(pdffilename):
    servePDF(pdffilename)
  else:
    print "Content-type: text/html"
    print
    print "<h1>Robo-Error: Error formatting route id: %s</h1>" % (route_id)
    print "<br>"
    print "<h2>Latex input:</h2>"
    print "<br>"
    sys.stdout.write(latex.replace("\n", "<br>"))
    print "<h2>Latex output:</h2>"
    sys.stdout.write(stdout.replace("\n", "<br>"))
finally:
  # Cleanup
  os.unlink(texfilename)
  if os.path.isfile(auxfilename):
    os.unlink(auxfilename)
  if os.path.isfile(logfilename):
    os.unlink(logfilename)


