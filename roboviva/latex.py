import cue
import re
  
def _makeClimb(climb_type):
  '''Very simple utility method -- provides a common way to specify climb types'''
  return r"$\underset{\text{" + climb_type + r"}}{\text{\Mountain}}$"

def _instructionToLatex(instruction, modifier):
  '''Maps a cue.Instruction the latex that should be used to render it'''
  if instruction == cue.Instruction.CAT_1:
    return _makeClimb("1")
  elif instruction == cue.Instruction.CAT_2:
    return _makeClimb("2")
  elif instruction == cue.Instruction.CAT_3:
    return _makeClimb("3")
  elif instruction == cue.Instruction.CAT_4:
    return _makeClimb("4")
  elif instruction == cue.Instruction.CAT_5:
    return _makeClimb("5")
  elif instruction == cue.Instruction.CAT_HC:
    return _makeClimb("HC")
  elif instruction == cue.Instruction.SUMMIT:
    return _makeClimb("END")
  elif instruction == cue.Instruction.DANGER:
    return r"\Large \danger "
  elif instruction == cue.Instruction.FIRST_AID:
    return r"\raisebox{-0.15em}{\Plus} "
  else:
    # all others can be rendered as-is, in bold:
    return r"\textbf{" + _escape(modifier) + _escape(instruction) + "}"

def _escape(text):
  r''' Escapes &, #, and other characters in 'text' so they don't break the
  latex render.'''
  ret = re.sub(r'\\([^\\]?)', r'\\textbackslash \1', text)
  ret = ret.replace("$", "\$")
  ret = ret.replace("#", "\#")
  ret = ret.replace("&", "\&")
  ret = ret.replace("|", r'$|$')
  ret = ret.replace("<", r'$<$')
  ret = ret.replace(">", r'$\Rightarrow$')
  ret = ret.replace("%", r'\%')
  ret = ret.replace('{', r'\{')
  ret = ret.replace('}', r'\}')
  return ret

def _format(text):
  '''Looks for markdown-style *emphasis* and **strong emphasis** in the text,
  turning it into \emph and \textbf, accordingly.'''

  # Step 0: Escape any whitespace-delimited *'s and **'s:
  text = re.sub(ur'\s\*\s', ur' \* ', text)
  text = re.sub(ur'\s\*\*\s', ur' \*\* ', text)

  # Do this in two passes. Each pass will replace **...** with \textbf{...},
  # and *...* with \emph{...}, where "..." DOES NOT CONTAIN ANY NESTED **...**
  # or *...* PATTERNS. We should do this to fixed point, but if people are
  # seriously doing this:
  # **Foo *bar **baz *foobar******
  # Screw 'em :)

  Num_Passes = 2
  for p in xrange(Num_Passes):
    text = re.sub(ur'(\*\*)(?!\s)((\\.|[^\\\*])*?[^\s\\])\1',
                  ur'\\textbf{\2}',
                  text)
    text = re.sub(ur'\*(?!\s)((\\.|[^\\\*])*?[^\s\\*])\*',
                  ur'\emph{\1}',
                  text)
  # Finally, un-escape any escaped *'s:
  text = re.sub(ur'\\(\*|_)', ur'\1', text)
  return text

def _entryColor(entry):
  '''Figures out what color, if any, this entry should have. Returns a color
  string, if appropriate, or 'None' if this entry doesn't need to be
  colored.'''
  # Figure out row color:
  color = None
  if entry.color == cue.Color.YELLOW:
    color = ur'{yellow}'
  elif entry.color == cue.Color.GRAY:
    color = ur'[gray]{0.7}'
  return color
  
def _entryToLatex(entry):
  '''Converts a cue.Entry into a latex supertabular row string'''

  color_str = ""
  note_str  = ""
  for_str   = ""
  color = _entryColor(entry)

  # Escape all user-provided strings:
  esc_note        = _escape(entry.note)
  esc_description = _escape(entry.description)

  if color:
    color_str = ur'\rowcolor%s' % color
  if entry.note:
    note_str = ur' \newline \textbf{Note:} %s' % esc_note 
  if entry.for_distance:
    for_str = "%5.1f" % entry.for_distance

  instruction_str = _instructionToLatex(entry.instruction, entry.modifier)
  note_str        = _format(note_str)
  description_str = _format(esc_description)
  return r"%s %s & %5.1f & %s%s & %s \\ \hline" % (color_str,
                                                   instruction_str,
                                                   entry.absolute_distance,
                                                   description_str,
                                                   note_str,
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
\usepackage{colortbl}
\usepackage{supertabular}
\usepackage{amsmath}
\usepackage{helvet}
\usepackage{fourier}
\usepackage{bbding}
\usepackage[alpine]{ifsym}
\renewcommand{\familydefault}{\sfdefault}

\begin{document}
  \twocolumn
    \tabletail{\hline}
      \tablelasttail{\hline}
        \begin{supertabular}{|c|p{0.35in}|p{2.25in}|l|}

        \hline
        \rowcolor[gray]{0}
        \textbf{\textcolor{white}{Go}}&\textbf{\textcolor{white}{At}}&\textbf{\textcolor{white}{On}}&\textbf{\textcolor{white}{For}}\\\hline
''')

LatexFooter = unicode(r'''
\end{supertabular}
\end{document} 
''')

