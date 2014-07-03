import csv
import enum

'''The action a particular cue entry represents'''
Instruction = enum.Enum(LEFT        = "L",
                        RIGHT       = "R",
                        STRAIGHT    = "S",
                        PIT         = "PIT",
                        DANGER      = "!",
                        CROSSES     = "X",
                        NONE        = "")

'''An instruction modifier. Only really makes sense for LEFT and RIGHT, at the moment'''
Modifier = enum.Enum(NONE   = "",
                     SLIGHT = "B",
                     QUICK  = "Q")

class Entry(object):
  '''Simple storage class representing a single cue sheet entry. Nothing fancy.'''
  def __init__(self, 
              instruction,
              description,
              absolute_distance,
              note         = "",
              modifier     = Modifier.NONE,
              for_distance = None):
    ''' Inits a CueEntry.
        instruction       - The entry's Instruction (see above)
        description       - The entry's 'action' (e.g., 'Turn right on Pine St')
        absolute_distance - How far this entry is from the ride's start (miles)
        note              - Optional. Any additional notes on this entry.
        modifier          - Optional. A Modifier to apply to the Instruction.
        for_distance      - Optional. How long from this entry to the next entry.
    '''
    self.instruction       = instruction
    self.description       = description
    self.absolute_distance = float(absolute_distance)
    self.note              = note
    self.modifier          = modifier
    self.for_distance      = for_distance

  def __repr__(self):
    for_str = ""
    if self.for_distance:
      for_str = "%5.2f" % self.for_distance
    else:
      for_str = "     "

    return "Entry[%s%s | %5.2f | %s | %s | %s]" % (self.modifier, 
                                                   self.instruction,
                                                   self.absolute_distance,
                                                   for_str,
                                                   self.description,
                                                   self.note)



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
