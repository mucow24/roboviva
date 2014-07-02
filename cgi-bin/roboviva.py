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

cgitb.enable()
fields = cgi.FieldStorage()

if 'routeid' not in fields:
  raise Error("No route ID specified")

route_id = fields['routeid'].value

url = 'http://ridewithgps.com/routes/%s.csv' % route_id
csv_data = []
try:
  csv_data = urllib2.urlopen(url).read()
except:
  print "Content-type: text/html"
  print
  print "<H1>Robo-Error: Invalid route ID: %s</H1>" % route_id
  sys.exit(0)

csv_rows = cue.processRows(csv_data.split('\n'))

latex = cue.LatexHeader
for row in csv_rows:
  latex = latex + cue.formatRow(row) + "\n"
latex = latex + cue.LatexFooter

#tempdir = tempfile.mkdtemp(dir='/tmp/')
# tempfile = tempfile.NamedTemporaryFile(delete=False)
# tempfilename = tempfile.name
os.chdir("/tmp/")
filenamebase = route_id
texfile = "%s.tex" % filenamebase
pdffile = "%s.pdf" % filenamebase
tempfile = open(texfile, 'w')
tempfile.write(latex)
tempfile.close()

try:
  p = subprocess.Popen(["/usr/bin/pdflatex", "-interaction=nonstopmode",  texfile], stdout=subprocess.PIPE)
  stdout, stderr = p.communicate()
  sys.stdout.write( "Content-type: application/pdf\r\n\r\n" + file(pdffile,"rb").read() )
finally:
  os.unlink(pdffile)
  os.unlink(texfile)


