import sys
from roboviva import ridewithgps
from roboviva import latex
from roboviva import tex

def main(argv):
  if len(argv) != 2:
    print "Usage: %s route_id" % argv[0]
    return 1

  route_id = int(argv[1])
  print "Downloading route from ridewithgps...",
  md5, cues = ridewithgps.getMd5AndCueSheet(route_id)
  print " Done [md5: %s]" % md5
  print "Generating latex...",
  src = latex.makeLatex(cues)
  print " Done."
  filename = "%s.pdf" % route_id
  print "Rendering PDF to '%s'..." % filename,
  with open(filename, 'wb') as pdf_file:
    pdf_file.write(tex.latex2pdf(src))
  print " Done."

if __name__ == "__main__":
  sys.exit(main(sys.argv))
