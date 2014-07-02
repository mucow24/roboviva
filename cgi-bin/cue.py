import csv

LatexHeader = r'''
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
'''

LatexFooter = r'''
\end{supertabular}
\end{document} 
'''

def processRows(csv_line_array):
  rows = []
  reader = csv.DictReader(csv_line_array, ['type', 'note', 'absolute_distance', 'elevation', 'description'])
  rows = [row for row in reader]

  # Prune header:
  rows = rows[1:]

  # Compute relative distances:
  dist = 0.0
  for i, row in enumerate(rows):
    if i is 0:
      continue
    row_dist = float(row['absolute_distance'])
    rel_dist = row_dist - dist
    rows[i - 1]['for'] = rel_dist
    rows[i]['for'] = None
    if rel_dist < 0.10:
      rows[i]['quick'] = True
    else:
      rows[i]['quick'] = False
    dist = row_dist

  for i, row in enumerate(rows):
    # Normalize Directions:
    dir_map = { "Right"    : "R",
                "Left"     : "L",
                "Straight" : "S",
                "Food"     : "PIT",
                "Water"    : "PIT",
                "Danger"   : "!"}
    typ = row['type']
    if typ in dir_map:
      typ = dir_map[typ]
    else:
      typ = typ[0]
    row['color'] = None

    if typ in ('R', 'L'):
      if typ is 'L':
        row['color'] = '[gray]{0.7}'

      if "Keep" in row['note']:
        typ = "B%s" % typ
      elif row['quick']:
        typ = "Q%s" % typ
      elif "Slight" in row['note']:
        typ = "B%s" % typ 
    
    if typ in ('!', 'PIT') or row['description']:
      row['color'] = '{yellow}'

    row['type'] = typ
  
    # Remove extraneous infro from notes:
    row['note'] = row['note'].replace("Slight left toward", "")
    row['note'] = row['note'].replace("Slight right toward ", "")
    row['note'] = row['note'].replace("Slight left onto ", "")
    row['note'] = row['note'].replace("Slight right onto ", "")
    row['note'] = row['note'].replace("Turn left onto ", "")
    row['note'] = row['note'].replace("Turn right onto ", "")
    row['note'] = row['note'].replace("Slight left to stay on ", "TRO ")
    row['note'] = row['note'].replace("Slight right to stay on ", "TRO ")
    row['note'] = row['note'].replace("Turn left to stay on ", "TRO ")
    row['note'] = row['note'].replace("Turn right to stay on ", "TRO ")
    row['note'] = row['note'].replace("Keep left to stay on ", "TRO ")
    row['note'] = row['note'].replace("Keep right to stay on ", "TRO ")
    row['note'] = row['note'].replace("At the traffic circle, ", "@ Circle, ") 
    row['note'] = row['note'].replace("Keep right at the fork", "At fork") 
    row['note'] = row['note'].replace("Keep left at the fork", "At fork") 
    row['note'] = row['note'].replace("Slight left ", "")
    row['note'] = row['note'].replace("Slight right ", "")
    row['note'] = row['note'].replace("Turn left ", "")
    row['note'] = row['note'].replace("Turn right ", "")
    row['note'] = row['note'].replace("Left onto ", "")
    row['note'] = row['note'].replace("Right onto ", "")
    row['note'] = row['note'].replace("Continue straight onto ", "")
    row['note'] = row['note'].replace("Continue onto ", "")

  return rows

def formatRow(row):
  ret = ""
  if row['color']:
    ret = ret + r"\rowcolor%s" % row['color']
  if not row['for']:
    row['for'] = 0
  
  text = row['note']
  if row['description']:
    text = text + r"\newline \textbf{Note:} %s" % row['description']
  ret = ret + r"\textbf{%s}&%.1f&%s&%.1f\\\hline" % (row['type'],
         float(row['absolute_distance']),
         text,
         row['for'])
  return ret 


def formatRows(rows):
  print LatexHeader
  for r in rows[1:]:
    print formatRow(r)
  print LatexFooter
