import cue
import csv
import urllib2
import hashlib
import re

class RideWithGpsError(Exception):
  '''Thrown by getCueSheet() in the event of an error'''
  pass

def getMd5AndCueSheet(route_id):
  '''
      Queries RideWithGPS, and returns a list of CueEntrys, along with the MD5
      checksum of the raw CSV data that generated it.

      route_id - The numeric route ID to fetch. (e.g. '12345' in ridewithgps.com/routes/12345)

      Throws a RideWithGpsError in the event of a problem (invalid route id, etc.)
  '''
  url = "http://ridewithgps.com/routes/%s.csv" % route_id

  raw_csv = ""
  try:
    raw_csv = urllib2.urlopen(url, timeout=5).read()
  except HTTPError as e:
    if e.code is 404:
      raise RideWithGpsError("Invalid Route ID")
    else:
      raise RideWithGpsError(e.reason)

  # Compute raw csv MD5:
  md5 = hashlib.md5(raw_csv).hexdigest()
  
  # Process CSV rows:
  reader = csv.DictReader(raw_csv.split("\n"),
                          ['type', 'note', 'absolute_distance', 'elevation', 'description'])
  rows   = [row for row in reader]

  # Compute "for" distances:
  distance_so_far = 0.0
  cue_rows = []
  for i, row in enumerate(rows):
    row['for_distance'] = None
    if i is 0 or i is 1:
      # Header row or start of route, skip entirely.
      continue
    # On >= second instruction
    rel_dist                    = float(row['absolute_distance']) - distance_so_far
    rows[i - 1]['for_distance'] = rel_dist
    distance_so_far             = float(row['absolute_distance']) 
  # [1:] to skip header line
  return (md5, [csvRowToCueEntry(row) for row in rows[1:]])
  



def cleanDescription(description):
  ''' 
    Clean up the description.

    RWGPS Duplicates the instruction in the description, e.g. "Right on Foo
    St.", instead of "Foo St.". This blows up the "On" column in the final
    sheet, so try to fix it as best we can.

    description - the original ridewithgps description string, e.g. "Turn right onto Foo St."
  '''
  description = re.sub("^At the traffic circle,",                     "@ Circle,", description)
  description = re.sub("^(Slight|Turn) (left|right) (toward|onto) ",   "",         description)
  description = re.sub("^(Slight|Turn|Keep) (left|right) to stay on",  "TRO",      description)
  description = re.sub("to stay on",                                   "TRO",      description)
  description = re.sub("to remain on",                                 "TRO",      description)
  description = re.sub("^(Slight|Turn|Bear) (left|right) ",            "",         description)
  description = re.sub("^(Left|Right) onto ",                          "",         description)
  description = re.sub("^Continue onto ",                              "",         description)
  description = re.sub("^Continue straight onto ",                     "",         description)
  return description

def csvRowToCueEntry(csv_row):
  '''Converts a ridewithgps CSV row into a cue.CueEntry. Assumes the following CSV layout:
     type,note,distance,elevation,description

     With the following mapping:
     type              -> instruction
     note              -> description
     absolute_distance -> absolute_distance
     for_distance      -> for_distance (Can be 'None')
     description       -> notes
  '''
  instruction_str = csv_row['type']
  description     = csv_row['note']
  distance        = float(csv_row['absolute_distance'])
  notes           = csv_row['description']
  for_distance    = csv_row['for_distance']

  # Figure out the (base) instruction:
  instruction = None
  if instruction_str == "Left":
    instruction = cue.Instruction.LEFT
  elif instruction_str == "Right":
    instruction = cue.Instruction.RIGHT
  elif instruction_str == "Straight":
    instruction = cue.Instruction.STRAIGHT
  elif instruction_str in ("Food", "Water"):
    instruction = cue.Instruction.PIT
  elif instruction_str == "Danger":
    instruction = cue.Instruction.DANGER
  elif instruction_str in ("Start", "End"):
    instruction = cue.Instruction.NONE
  else:
    # Just punt to whatever they gave us:
    instruction = instruction_str

  # See if we can apply any modifiers yet:
  modifier = cue.Modifier.NONE
  if instruction in (cue.Instruction.LEFT, cue.Instruction.RIGHT):
    # RWGPS will use the terms "Keep [left|right]" or "Bear [left|right]" to
    # indicate slight turns:
    if re.match("^(Keep|Bear|Slight) ", description):
      modifier = cue.Modifier.SLIGHT
    elif csv_row['for_distance'] and csv_row['for_distance'] < 0.1:
      # Call it "quick"
      modifier = cue.Modifier.QUICK

  return cue.Entry(instruction,
                   cleanDescription(description),
                   distance,
                   notes,
                   modifier,
                   for_distance)
