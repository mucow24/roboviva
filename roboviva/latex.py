import cue

def _escape(text):
  ''' Escapes &, #, and other characters in 'text' so they don't break the latex
  render. For now, \ is NOT escaped, in case you really need an integral in
  your cue sheet'''
  ret = text.replace("#", "\#")
  ret = ret.replace("&", "\&")
  ret = ret.replace("$", "\$")
  ret = ret.replace("|", r'$|$')
  ret = ret.replace("<", r'$<$')
  ret = ret.replace(">", r'$\Rightarrow$')
  return ret

def _entryToLatex(entry):
  '''Converts a cue.Entry into a latex supertabular row string'''
  
  # Figure out row color:
  color = None
  if (entry.instruction in (cue.Instruction.DANGER, cue.Instruction.PIT)) or entry.note:
    color = ur'{yellow}'
  elif entry.instruction == cue.Instruction.LEFT:
    color = ur'[gray]{0.7}'

  color_str = ""
  note_str  = ""
  for_str   = ""
  if color:
    color_str = ur'\rowcolor%s' % color
  if entry.note:
    note_str = ur' \newline \textbf{Note:} %s' % entry.note
  if entry.for_distance:
    for_str = "%5.1f" % entry.for_distance

  return r"%s \textbf{%s} & %5.1f & %s%s & %s \\ \hline" % (color_str,
                                                               entry.modifier + entry.instruction,
                                                               entry.absolute_distance,
                                                               _escape(entry.description),
                                                               _escape(note_str),
                                                               for_str)

def makeLatex(ents):
  ''' Makes a full latex document from an array of cue.Entry's
      ents - list of cue.Entry objects
  '''
  ret = LatexHeader
  for ent in ents:
    ret = ret + _entryToLatex(ent) + "\n"
  ret = ret + LatexFooter
  return ret

LatexHeader = unicode(r'''
\documentclass[11pt]{article}
\usepackage[left=0.25in,right=0.25in,top=0.25in,bottom=0.25in]{geometry}
\geometry{letterpaper} 
\usepackage{epstopdf}
\usepackage{colortbl}
\usepackage{supertabular}
\usepackage{helvet}

\renewcommand{\familydefault}{\sfdefault}

\begin{document}
  \twocolumn
    \tabletail{\hline}
      \tablelasttail{\hline}
        \begin{supertabular}{|p{0.25in}|p{0.35in}|p{2.25in}|l|}

        \hline
        \rowcolor[gray]{0}
        \textbf{\textcolor{white}{Go}}&\textbf{\textcolor{white}{At}}&\textbf{\textcolor{white}{On}}&\textbf{\textcolor{white}{For}}\\\hline
''')

LatexFooter = unicode(r'''
\end{supertabular}
\end{document} 
''')

