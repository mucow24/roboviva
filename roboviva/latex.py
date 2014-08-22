import cue

def _instructionToLatex(instruction, modifier):
  '''Maps a cue.Instruction the latex that should be used to render it'''
  if instruction == cue.Instruction.CAT_1:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{1}}$"
  elif instruction == cue.Instruction.CAT_2:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{2}}$"
  elif instruction == cue.Instruction.CAT_3:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{3}}$"
  elif instruction == cue.Instruction.CAT_4:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{4}}$"
  elif instruction == cue.Instruction.CAT_5:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{5}}$"
  elif instruction == cue.Instruction.CAT_HC:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{HC}}$"
  elif instruction == cue.Instruction.SUMMIT:
    return r"$\boldsymbol{\nearrow}_\text{\textbf{END}}$"
  else:
    # all others can be rendered as-is, in bold:
    return r"\textbf{" + modifier + instruction + "}"

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
  ret = ret.replace("%", r'\%')
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

  instruction_str = _instructionToLatex(entry.instruction, entry.modifier)
  return r"%s %s & %5.1f & %s%s & %s \\ \hline" % (color_str,
                                                   instruction_str,
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
\usepackage{amsmath}
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

